import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Protocol
from abc import ABC, abstractmethod
import json
import keyboard

from models.types import AppView, MQTTConfig
from utils.helpers import validate_mqtt_config, validate_room_id, validate_username, generate_room_id, format_timestamp
from ui.styles import StyleManager

from utils.riot import get_current_time, set_time

class ViewCallbacks(Protocol):
    def on_connect_requested(self, config: MQTTConfig) -> None: ...
    def on_mode_selected(self, mode: str) -> None: ...
    def on_room_joined(self, room_id: str, username: str) -> None: ...
    def on_sync_requested(self) -> None: ...
    def on_back_requested(self) -> None: ...
    def on_disconnect_requested(self) -> None: ...
    def on_assign_user(self, username: str, time_ms: int) -> None: ...
    def on_remove_user(self, username: str) -> None: ...
    def on_send_time_request(self, topic: str, payload: str) -> None: ...
    def on_send_time_response(self, topic: str, payload: str) -> None: ...


class BaseView(ABC):
    def __init__(self, parent: tk.Frame, style_manager: StyleManager, callbacks: ViewCallbacks) -> None:
        self.parent = parent
        self.style_manager = style_manager
        self.callbacks = callbacks
        self._widgets: list[tk.Widget] = []
    
    @abstractmethod
    def show(self) -> None:
        pass
    
    def hide(self) -> None:
        for widget in self._widgets:
            widget.destroy()
        self._widgets.clear()
    
    def _add_widget(self, widget: tk.Widget) -> None:
        self._widgets.append(widget)


class ConnectionView(BaseView):
    def __init__(self, parent: tk.Frame, style_manager: StyleManager, callbacks: ViewCallbacks) -> None:
        super().__init__(parent, style_manager, callbacks)
        self.url_entry: Optional[tk.Entry] = None
        self.port_entry: Optional[tk.Entry] = None
        self.status_label: Optional[tk.Label] = None
    
    def show(self) -> None:
        title_label = self.style_manager.create_label(self.parent, "ChronosPY", "title")
        title_label.pack(pady=(0, 10))
        self._add_widget(title_label)
        
        subtitle_label = self.style_manager.create_label(self.parent, "Connect to MQTT Broker", "subtitle")
        subtitle_label.pack(pady=(0, 30))
        self._add_widget(subtitle_label)
        
        connection_frame = self.style_manager.create_frame(self.parent)
        connection_frame.pack(pady=20)
        self._add_widget(connection_frame)
        
        url_label = self.style_manager.create_label(connection_frame, "Broker URL:", "normal")
        url_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=10)
        
        self.url_entry = self.style_manager.create_entry(connection_frame, 30)
        self.url_entry.grid(row=0, column=1, padx=(0, 0), pady=10)
        self.url_entry.insert(0, "localhost")
        
        port_label = self.style_manager.create_label(connection_frame, "Port:", "normal")
        port_label.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)
        
        self.port_entry = self.style_manager.create_entry(connection_frame, 30)
        self.port_entry.grid(row=1, column=1, padx=(0, 0), pady=10)
        self.port_entry.insert(0, "1883")
        
        connect_btn = self.style_manager.create_button(
            self.parent, "CONNECT", self._on_connect_clicked, "primary"
        )
        connect_btn.pack(pady=30)
        self._add_widget(connect_btn)
        
        self.status_label = self.style_manager.create_label(self.parent, "Disconnected", "status")
        self.status_label.pack(pady=10)
        self._add_widget(self.status_label)
    
    def update_status(self, status: str) -> None:
        if self.status_label:
            self.status_label.config(text=status)
    
    def _on_connect_clicked(self) -> None:
        if not self.url_entry or not self.port_entry:
            return
        
        url = self.url_entry.get().strip()
        port = self.port_entry.get().strip()
        
        is_valid, error_msg = validate_mqtt_config(url, port)
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
        
        config = MQTTConfig(url=url, port=int(port))
        self.callbacks.on_connect_requested(config)


class ModeSelectionView(BaseView):
    def show(self) -> None:
        title_label = self.style_manager.create_label(self.parent, "Select Mode", "title")
        title_label.pack(pady=(0, 30))
        self._add_widget(title_label)
        
        producer_btn = self.style_manager.create_button(
            self.parent, "CONNECT AS PRODUCER", 
            lambda: self.callbacks.on_mode_selected("producer"), "big"
        )
        producer_btn.pack(pady=20)
        self._add_widget(producer_btn)
        
        observer_btn = self.style_manager.create_button(
            self.parent, "CONNECT AS OBSERVER",
            lambda: self.callbacks.on_mode_selected("observer"), "big"
        )
        observer_btn.pack(pady=20)
        self._add_widget(observer_btn)
        
        back_btn = self.style_manager.create_button(
            self.parent, "Back to Connection", 
            self.callbacks.on_disconnect_requested, "secondary"
        )
        back_btn.pack(pady=(30, 0))
        self._add_widget(back_btn)


class ProducerView(BaseView):
    def __init__(self, parent: tk.Frame, style_manager: StyleManager, callbacks: ViewCallbacks) -> None:
        super().__init__(parent, style_manager, callbacks)
        self.room_id: Optional[str] = None
        self.connected_users: dict = {}
        self.users_frame: Optional[tk.Frame] = None
        self.main_observer_var: Optional[tk.StringVar] = None
    
    def show(self) -> None:
        self.room_id = generate_room_id()
        self.main_observer_var = tk.StringVar()
        
        title_label = self.style_manager.create_label(self.parent, "Producer Mode", "title")
        title_label.pack(pady=(0, 20))
        self._add_widget(title_label)
        
        room_frame = self.style_manager.create_frame(self.parent)
        room_frame.pack(pady=20)
        self._add_widget(room_frame)
        
        room_label = self.style_manager.create_label(room_frame, "Room ID:", "normal")
        room_label.pack(side="left", padx=(0, 10))
        
        room_id_label = self.style_manager.create_label(room_frame, self.room_id, "subtitle")
        room_id_label.pack(side="left")
        
        topic = f"{self.room_id}/#"
        sub_label = self.style_manager.create_label(self.parent, f"Subscribed to: {topic}", "normal")
        sub_label.pack(pady=10)
        self._add_widget(sub_label)
        
        users_label = self.style_manager.create_label(self.parent, "Connected Users:", "subtitle")
        users_label.pack(pady=(20, 10))
        self._add_widget(users_label)
        
        users_container = self.style_manager.create_frame(self.parent)
        users_container.pack(fill="both", expand=True, pady=10)
        self._add_widget(users_container)
        
        canvas = tk.Canvas(users_container, bg=self.style_manager.colors['bg_secondary'], height=200)
        scrollbar = ttk.Scrollbar(users_container, orient="vertical", command=canvas.yview)
        
        self.users_frame = self.style_manager.create_frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        canvas_window = canvas.create_window((0, 0), window=self.users_frame, anchor="nw")
        
        def configure_scroll_region(*args):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:
                canvas.itemconfig(canvas_window, width=canvas_width)
        
        self.users_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_scroll_region)
        
        back_btn = self.style_manager.create_button(
            self.parent, "Back", self.callbacks.on_back_requested, "secondary"
        )
        back_btn.pack(pady=10)
        self._add_widget(back_btn)
    
    def get_room_id(self) -> Optional[str]:
        return self.room_id
    
    def add_user(self, username: str) -> None:
        if username in self.connected_users or not self.users_frame or not self.main_observer_var:
            print(f"[DEBUG] Exiting add_user without adding user")
            return
        
        print(f"[DEBUG] Creating interface for user: {username}")
        
        user_frame = self.style_manager.create_frame(self.users_frame)
        user_frame.pack(fill="x", padx=5, pady=5)
        
        name_label = self.style_manager.create_label(user_frame, username, "normal")
        name_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        time_label = self.style_manager.create_label(user_frame, "Time (ms):", "normal")
        time_label.grid(row=0, column=1, padx=(0, 5))
        
        time_entry = self.style_manager.create_entry(user_frame, 10)
        time_entry.grid(row=0, column=2, padx=(0, 10))
        time_entry.insert(0, "1000")
        
        main_radio = ttk.Radiobutton(
            user_frame, 
            text="MAIN OBSERVER", 
            variable=self.main_observer_var, 
            value=username,
            style="Custom.TRadiobutton"
        )
        main_radio.grid(row=0, column=3, padx=(0, 10))
        
        assign_btn = self.style_manager.create_button(
            user_frame, "Assign", 
            lambda u=username: self._on_assign_clicked(u), "primary"
        )
        assign_btn.grid(row=0, column=4, padx=(0, 5))
        
        remove_btn = self.style_manager.create_button(
            user_frame, "✕", lambda u=username: self.remove_user(u), "secondary"
        )
        remove_btn.grid(row=0, column=5)
        
        self.connected_users[username] = {
            "time_entry": time_entry,
            "main_var": self.main_observer_var,
            "frame": user_frame
        }
        
        print(f"[DEBUG] User {username} added successfully. Total users: {len(self.connected_users)}")
    
    def remove_user(self, username: str) -> None:
        if username not in self.connected_users:
            return
        
        user_data = self.connected_users[username]
        user_data["frame"].destroy()
        
        if self.main_observer_var and self.main_observer_var.get() == username:
            self.main_observer_var.set("")
        
        del self.connected_users[username]
    
    def get_user_time(self, username: str) -> Optional[int]:
        if username not in self.connected_users:
            return None
        
        try:
            time_str = self.connected_users[username]["time_entry"].get()
            return int(time_str)
        except ValueError:
            return 1000
    
    def get_main_observer(self) -> Optional[str]:
        if self.main_observer_var:
            main = self.main_observer_var.get()
            return main if main else None
        return None
    
    def get_all_users_config(self) -> dict:
        config = {}
        for username in self.connected_users:
            config[username] = {
                "time_ms": self.get_user_time(username),
                "is_main_observer": username == self.get_main_observer()
            }
        return config
    
    def _on_assign_clicked(self, username: str) -> None:
        time_ms = self.get_user_time(username)
        if time_ms is not None:
            self.callbacks.on_assign_user(username, time_ms)
    
    def add_message(self, topic: str, payload: str, timestamp: str) -> None:
        print(f"[DEBUG] ProducerView.add_message called:")
        print(f"  Topic: {topic}")
        print(f"  Payload: {payload}")
        
        try:
            data = json.loads(payload)
            print(f"[DEBUG] JSON parsed successfully: {data}")
            
            action = data.get("action")
            print(f"[DEBUG] Action extracted: {action}")
            
            if action == "SYNC_REQ":
                print(f"[DEBUG] Processing SYNC_REQ")
                self._handle_sync_request(topic)
                
            elif action in ["JOIN", "LEAVE"]:
                print(f"[DEBUG] Processing action {action}")
                
                parts = topic.split("/")
                print(f"[DEBUG] Topic parts: {parts}")
                
                if len(parts) >= 2:
                    username = parts[-1]
                    print(f"[DEBUG] Username extracted: {username}")
                    
                    if action == "JOIN":
                        print(f"[DEBUG] Adding user: {username}")
                        self.add_user(username)
                    elif action == "LEAVE":
                        print(f"[DEBUG] Removing user: {username}")
                        self.remove_user(username)
                else:
                    print(f"[DEBUG] Topic doesn't have enough parts: {len(parts)}")
            else:
                print(f"[DEBUG] Unrecognized action: {action}")
                        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[DEBUG] Error parsing JSON or missing action: {str(e)}")
            pass
    
    def _handle_sync_request(self, topic: str) -> None:
        print(f"[DEBUG] Handling SYNC_REQ from topic: {topic}")
        
        parts = topic.split("/")
        if len(parts) < 2:
            print(f"[DEBUG] Topic has incorrect format: {topic}")
            return
        
        requester = parts[-1]
        print(f"[DEBUG] Requester extracted: {requester}")
        
        main_observer = self.get_main_observer()
        print(f"[DEBUG] Current MAIN OBSERVER: {main_observer}")
        
        if not main_observer:
            print(f"[DEBUG] No MAIN OBSERVER configured")
            return
        
        if not self.room_id:
            print(f"[DEBUG] No room_id available")
            return
        
        requester_delay = self.get_user_time(requester)
        main_observer_delay = self.get_user_time(main_observer)
        
        print(f"[DEBUG] Requester delay: {requester_delay}ms")
        print(f"[DEBUG] Main observer delay: {main_observer_delay}ms")
        
        if requester_delay is None:
            print(f"[DEBUG] Could not get requester delay: {requester}")
            requester_delay = 1000
        
        if main_observer_delay is None:
            print(f"[DEBUG] Could not get main observer delay: {main_observer}")
            main_observer_delay = 1000
        
        time_req_topic = f"{self.room_id}/{main_observer}"
        time_req_payload = json.dumps({
            "action": "TIME_REQ",
            "requester": requester,
            "requester_delay": requester_delay,
            "main_observer_delay": main_observer_delay
        })
        
        print(f"[DEBUG] Sending TIME_REQ:")
        print(f"  Topic: {time_req_topic}")
        print(f"  Payload: {time_req_payload}")
        print(f"  Requester: {requester} ({requester_delay}ms)")
        print(f"  Main Observer: {main_observer} ({main_observer_delay}ms)")
        
        self.callbacks.on_send_time_request(time_req_topic, time_req_payload)


class ObserverView(BaseView):
    def __init__(self, parent: tk.Frame, style_manager: StyleManager, callbacks: ViewCallbacks) -> None:
        super().__init__(parent, style_manager, callbacks)
        self.room_entry: Optional[tk.Entry] = None
        self.username_entry: Optional[tk.Entry] = None
        self.join_status_label: Optional[tk.Label] = None
        self.sync_btn: Optional[tk.Button] = None
        self.messages_text: Optional[tk.Text] = None
        self.current_room_id: Optional[str] = None
        self.current_username: Optional[str] = None
        keyboard.add_hotkey('alt+ctrl+t', self._on_hotkey_sync, suppress=True)
    
    def show(self) -> None:
        title_label = self.style_manager.create_label(self.parent, "Observer Mode", "title")
        title_label.pack(pady=(0, 30))
        self._add_widget(title_label)
        
        room_frame = self.style_manager.create_frame(self.parent)
        room_frame.pack(pady=20)
        self._add_widget(room_frame)
        
        room_label = self.style_manager.create_label(room_frame, "Room ID:", "normal")
        room_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=10)
        
        self.room_entry = self.style_manager.create_entry(room_frame, 20)
        self.room_entry.grid(row=0, column=1, padx=(0, 10), pady=10)
        
        username_label = self.style_manager.create_label(room_frame, "Username:", "normal")
        username_label.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)
        
        self.username_entry = self.style_manager.create_entry(room_frame, 20)
        self.username_entry.grid(row=1, column=1, padx=(0, 10), pady=10)
        
        join_btn = self.style_manager.create_button(
            room_frame, "JOIN", self._on_join_clicked, "primary"
        )
        join_btn.grid(row=0, column=2, rowspan=2, pady=10)
            
        info_label = self.style_manager.create_label(
            self.parent, 
            "Username: letters, numbers and hyphens only (3-20 characters)\nHotkey: Alt + Ctrl + T to sync", 
            "normal"
        )
        info_label.pack(pady=5)
        self._add_widget(info_label)
        
        self.join_status_label = self.style_manager.create_label(self.parent, "", "status")
        self.join_status_label.pack(pady=10)
        self._add_widget(self.join_status_label)
        
        self.sync_btn = self.style_manager.create_button(
            self.parent, "SYNC", self.callbacks.on_sync_requested, "big", "disabled"
        )
        self.sync_btn.pack(pady=30)
        self._add_widget(self.sync_btn)

        back_btn = self.style_manager.create_button(
            self.parent, "Back", self.callbacks.on_back_requested, "secondary"
        )
        back_btn.pack(pady=10)
        self._add_widget(back_btn)
    
    def _on_join_clicked(self) -> None:
        if not self.room_entry or not self.username_entry:
            return
        
        room_id = self.room_entry.get().strip().upper()
        username = self.username_entry.get().strip()
        
        if not validate_room_id(room_id):
            messagebox.showerror("Error", "Room ID must be 5 alphanumeric characters")
            return
        
        if not validate_username(username):
            messagebox.showerror(
                "Error", 
                "Username must be 3-20 characters and can only contain letters, numbers and hyphens"
            )
            return
        
        self.current_room_id = room_id
        self.current_username = username
        self.callbacks.on_room_joined(room_id, username)
    
    def update_join_status(self, room_id: str, username: str) -> None:
        if self.join_status_label:
            self.join_status_label.config(text=f"Connected to room: {room_id} as {username}")
        if self.sync_btn:
            self.sync_btn.config(state="normal")
    
    def get_current_room_id(self) -> Optional[str]:
        return self.current_room_id
    
    def get_current_username(self) -> Optional[str]:
        return self.current_username
    
    def add_sent_message(self, topic: str, payload: str, timestamp: str) -> None:
        if self.messages_text:
            message = f"[{timestamp}] Sent to {topic}: {payload}\n"
            self.messages_text.config(state="normal")
            self.messages_text.insert("end", message)
            self.messages_text.see("end")
            self.messages_text.config(state="disabled")
    
    def add_received_message(self, topic: str, payload: str, timestamp: str) -> None:
        print(f"[DEBUG] ObserverView.add_received_message:")
        print(f"  Topic: {topic}")
        print(f"  Payload: {payload}")
        
        try:
            data = json.loads(payload)
            action = data.get("action")
            
            print(f"[DEBUG] Observer processing action: {action}")
            
            if action == "TIME_REQ":
                requester = data.get("requester", "unknown")
                requester_delay = data.get("requester_delay", 0)
                main_observer_delay = data.get("main_observer_delay", 0)
                
                print(f"[DEBUG] Observer received TIME_REQ:")
                print(f"  Requester: {requester}")
                print(f"  Requester delay: {requester_delay}ms")
                print(f"  Main observer delay: {main_observer_delay}ms")
                print(f"[DEBUG] Sending TIME_RESPONSE...")
                
                self._handle_time_request(topic, requester, requester_delay, main_observer_delay)
                
            elif action == "ASSIGN":
                time_ms = data.get("time_ms", 0)
                print(f"[DEBUG] Observer received ASSIGN with time: {time_ms}ms")
                
            elif action == "SYNC_RESPONSE":
                time_value = data.get("value", 0)
                print(f"[DEBUG] Observer received SYNC_RESPONSE with time: {time_value}")
                set_time(time_value)
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[DEBUG] Observer: Error parsing message: {str(e)}")

    def _handle_time_request(self, original_topic: str, requester: str, requester_delay: int, main_observer_delay: int) -> None:
        if not self.current_room_id or not self.current_username:
            print(f"[DEBUG] No current room or username to respond to TIME_REQ")
            return
        
        actual_time = get_current_time()

        response_topic = f"{self.current_room_id}/{requester}"
        response_payload = json.dumps({
            "action": "SYNC_RESPONSE",
            "value": (actual_time + requester_delay - main_observer_delay)/1000
        })
        
        print(f"[DEBUG] Sending SYNC_RESPONSE:")
        print(f"  Topic: {response_topic}")
        print(f"  Payload: {response_payload}")
        
        self.callbacks.on_send_time_response(response_topic, response_payload)

    def _on_hotkey_sync(self) -> None:
        if self.sync_btn and self.sync_btn["state"] != "disabled":
            self.callbacks.on_sync_requested()

    def hide(self) -> None:
        keyboard.remove_hotkey('alt+ctrl+t')
        super().hide() 