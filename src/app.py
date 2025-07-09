import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any
import json
import time

from models.types import AppView, MQTTConfig, ConnectionStatus
from ui.styles import StyleManager
from ui.views import (
    ViewCallbacks, ConnectionView, ModeSelectionView, 
    ProducerView, ObserverView
)
from mqtt.client import MQTTManager
from utils.helpers import format_timestamp


class ChronosPYApp:
    """Main ChronosPY application with complete type hints"""
    
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._setup_window()
        
        # Managers
        self.style_manager = StyleManager()
        self.mqtt_manager = MQTTManager()
        
        # Application state
        self.current_view: AppView = AppView.CONNECTION
        self.connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
        
        # UI
        self.main_frame = tk.Frame(root, bg=self.style_manager.colors['bg_primary'])
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Views
        self.views: Dict[AppView, Any] = {}
        self._setup_views()
        self._setup_mqtt_callbacks()
        
        # Show initial view
        self._show_view(AppView.CONNECTION)
    
    def _setup_window(self) -> None:
        """Configure main window"""
        self.root.title("ChronosPY - MQTT Controller")
        self.root.geometry("600x500")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)
        
        # Configure window close behavior
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_closing)
    
    def _setup_views(self) -> None:
        """Configure all views"""
        callbacks = ViewCallbacksImpl(self)
        
        self.views[AppView.CONNECTION] = ConnectionView(
            self.main_frame, self.style_manager, callbacks
        )
        self.views[AppView.MODE_SELECTION] = ModeSelectionView(
            self.main_frame, self.style_manager, callbacks
        )
        self.views[AppView.PRODUCER] = ProducerView(
            self.main_frame, self.style_manager, callbacks
        )
        self.views[AppView.OBSERVER] = ObserverView(
            self.main_frame, self.style_manager, callbacks
        )
    
    def _setup_mqtt_callbacks(self) -> None:
        """Configure MQTT callbacks"""
        self.mqtt_manager.set_connection_callback(self._on_mqtt_connection_changed)
        self.mqtt_manager.set_message_callback(self._on_mqtt_message_received)
    
    def _show_view(self, view: AppView) -> None:
        """
        Show a specific view.
        
        Args:
            view: View to display
        """
        # Hide current view
        if self.current_view in self.views:
            self.views[self.current_view].hide()
        
        # Show new view
        self.current_view = view
        if view in self.views:
            self.views[view].show()
    
    def _on_mqtt_connection_changed(self, is_connected: bool) -> None:
        """
        Callback for MQTT connection changes.
        
        Args:
            is_connected: Connection state
        """
        if is_connected:
            self.connection_status = ConnectionStatus.CONNECTED
            self._update_connection_status("Successfully connected")
            # Change to mode selection after 1 second
            self.root.after(1000, lambda: self._show_view(AppView.MODE_SELECTION))
        else:
            self.connection_status = ConnectionStatus.DISCONNECTED
            self._update_connection_status("Disconnected")
    
    def _on_mqtt_message_received(self, topic: str, payload: str, timestamp: str) -> None:
        """
        Callback for received MQTT messages.
        
        Args:
            topic: Message topic
            payload: Message content
            timestamp: Message timestamp
        """
        print(f"[DEBUG] MQTT message received:")
        print(f"  Topic: {topic}")
        print(f"  Payload: {payload}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Current view: {self.current_view}")
        
        # Process according to active view
        if self.current_view == AppView.PRODUCER:
            print(f"[DEBUG] Processing message in PRODUCER view")
            producer_view = self.views[AppView.PRODUCER]
            producer_view.add_message(topic, payload, timestamp)
            
        elif self.current_view == AppView.OBSERVER:
            print(f"[DEBUG] Processing message in OBSERVER view")
            observer_view = self.views[AppView.OBSERVER]
            observer_view.add_received_message(topic, payload, timestamp)
    
    def _update_connection_status(self, status: str) -> None:
        """
        Update status in connection view.
        
        Args:
            status: Status message
        """
        if AppView.CONNECTION in self.views:
            connection_view = self.views[AppView.CONNECTION]
            connection_view.update_status(status)
    
    def _on_window_closing(self) -> None:
        """Handle window closing"""
        # If we're in observer view and a user is connected, send LEAVE
        if self.current_view == AppView.OBSERVER and self.mqtt_manager.is_connected:
            observer_view = self.views[AppView.OBSERVER]
            room_id = observer_view.get_current_room_id()
            username = observer_view.get_current_username()
            
            if room_id and username:
                try:
                    # Send JSON message with LEAVE action
                    topic = f"{room_id}/{username}"
                    payload = json.dumps({"action": "LEAVE"})
                    
                    self.mqtt_manager.publish(topic, payload)
                    
                    # Give some time for the message to be sent
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error sending LEAVE message: {str(e)}")
        
        if self.mqtt_manager.is_connected:
            self.mqtt_manager.disconnect()
        self.root.destroy()


class ViewCallbacksImpl:
    """Implementation of view callbacks"""
    
    def __init__(self, app: ChronosPYApp) -> None:
        self.app = app
    
    def on_connect_requested(self, config: MQTTConfig) -> None:
        """Handle connection request"""
        try:
            self.app._update_connection_status("Connecting...")
            self.app.root.update()
            self.app.mqtt_manager.connect(config)
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.app._update_connection_status("Connection error")
    
    def on_mode_selected(self, mode: str) -> None:
        """Handle mode selection"""
        if mode == "producer":
            self.app._show_view(AppView.PRODUCER)
            self._setup_producer_mode()
        elif mode == "observer":
            self.app._show_view(AppView.OBSERVER)
    
    def on_room_joined(self, room_id: str, username: str) -> None:
        """Handle room join"""
        try:
            print(f"[DEBUG] Observer joining room:")
            print(f"  Room ID: {room_id}")
            print(f"  Username: {username}")
            
            observer_view = self.app.views[AppView.OBSERVER]
            observer_view.update_join_status(room_id, username)
            
            # Subscribe to user's topic
            topic = f"{room_id}/{username}"
            print(f"[DEBUG] Observer subscribing to topic: {topic}")
            self.app.mqtt_manager.subscribe(topic)
            
            # Send JSON message with JOIN action
            payload = json.dumps({"action": "JOIN"})
            print(f"[DEBUG] Observer sending message:")
            print(f"  Topic: {topic}")
            print(f"  Payload: {payload}")
            
            self.app.mqtt_manager.publish(topic, payload)
            print(f"[DEBUG] JOIN message sent successfully")
            
            # Show sent message in interface
            timestamp = format_timestamp()
            observer_view.add_sent_message(topic, payload, timestamp)
            
        except Exception as e:
            print(f"[DEBUG] Error in on_room_joined: {str(e)}")
            messagebox.showerror("Error", f"Error sending join message: {str(e)}")
    
    def on_sync_requested(self) -> None:
        """Handle synchronization request"""
        try:
            observer_view = self.app.views[AppView.OBSERVER]
            room_id = observer_view.get_current_room_id()
            username = observer_view.get_current_username()
            
            if not room_id or not username:
                messagebox.showerror("Error", "You must join a room first")
                return
            
            print(f"[DEBUG] Sending sync request:")
            print(f"  Room ID: {room_id}")
            print(f"  Username: {username}")
            
            # Send sync message
            sync_message = self.app.mqtt_manager.publish_sync_message(room_id, username)
            
            # Show in interface
            timestamp = format_timestamp()
            topic = f"{room_id}/{username}"
            payload = json.dumps({"action": "SYNC_REQ"})
            
            observer_view.add_sent_message(topic, payload, timestamp)
            
        except Exception as e:
            print(f"[DEBUG] Error in on_sync_requested: {str(e)}")
            messagebox.showerror("Error", f"Error sending message: {str(e)}")
    
    def on_back_requested(self) -> None:
        """Handle back request"""
        # If we're in observer view and a user is connected, send LEAVE
        if self.app.current_view == AppView.OBSERVER:
            observer_view = self.app.views[AppView.OBSERVER]
            room_id = observer_view.get_current_room_id()
            username = observer_view.get_current_username()
            
            if room_id and username:
                try:
                    # Send JSON message with LEAVE action
                    topic = f"{room_id}/{username}"
                    payload = json.dumps({"action": "LEAVE"})
                    
                    self.app.mqtt_manager.publish(topic, payload)
                    
                except Exception as e:
                    # Don't show error to user since they're leaving, just log
                    print(f"Error sending LEAVE message: {str(e)}")
        
        self.app._show_view(AppView.MODE_SELECTION)
    
    def on_disconnect_requested(self) -> None:
        """Handle disconnect request"""
        # If we're in observer view and a user is connected, send LEAVE
        if self.app.current_view == AppView.OBSERVER:
            observer_view = self.app.views[AppView.OBSERVER]
            room_id = observer_view.get_current_room_id()
            username = observer_view.get_current_username()
            
            if room_id and username:
                try:
                    # Send JSON message with LEAVE action
                    topic = f"{room_id}/{username}"
                    payload = json.dumps({"action": "LEAVE"})
                    
                    self.app.mqtt_manager.publish(topic, payload)
                    
                except Exception as e:
                    print(f"Error sending LEAVE message: {str(e)}")
        
        self.app.mqtt_manager.disconnect()
        self.app._show_view(AppView.CONNECTION)
    
    def _setup_producer_mode(self) -> None:
        """Configure producer mode"""
        producer_view = self.app.views[AppView.PRODUCER]
        room_id = producer_view.get_room_id()
        
        print(f"[DEBUG] Setting up producer mode")
        print(f"  Room ID: {room_id}")
        
        if room_id:
            # Subscribe to room topic
            topic = f"{room_id}/#"
            print(f"[DEBUG] Subscribing to topic: {topic}")
            try:
                self.app.mqtt_manager.subscribe(topic)
                print(f"[DEBUG] Successfully subscribed to topic: {topic}")
            except Exception as e:
                print(f"[DEBUG] Subscription error: {str(e)}")
                messagebox.showerror("Error", f"Error subscribing to topic: {str(e)}")
        else:
            print(f"[DEBUG] No room_id available")
    
    def on_assign_user(self, username: str, time_ms: int) -> None:
        """Handle user time assignment"""
        try:
            if self.app.current_view == AppView.PRODUCER:
                producer_view = self.app.views[AppView.PRODUCER]
                room_id = producer_view.get_room_id()
                
                if room_id and username:
                    # Send assignment message
                    topic = f"{room_id}/{username}"
                    payload = json.dumps({
                        "action": "ASSIGN",
                        "time_ms": time_ms
                    })
                    
                    self.app.mqtt_manager.publish(topic, payload)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error sending assignment: {str(e)}")
    
    def on_remove_user(self, username: str) -> None:
        """Handle manual user removal"""
        try:
            if self.app.current_view == AppView.PRODUCER:
                producer_view = self.app.views[AppView.PRODUCER]
                room_id = producer_view.get_room_id()
                
                if room_id and username:
                    # Send forced LEAVE message
                    topic = f"{room_id}/{username}"
                    payload = json.dumps({"action": "LEAVE"})
                    
                    self.app.mqtt_manager.publish(topic, payload)
                    
                    # Remove from local list
                    producer_view.remove_user(username)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error removing user: {str(e)}")
    
    def on_send_time_request(self, topic: str, payload: str) -> None:
        """Handle TIME_REQ sending from producer"""
        try:
            print(f"[DEBUG] Sending TIME_REQ via MQTT:")
            print(f"  Topic: {topic}")
            print(f"  Payload: {payload}")
            
            self.app.mqtt_manager.publish(topic, payload)
            print(f"[DEBUG] TIME_REQ sent successfully")
            
        except Exception as e:
            print(f"[DEBUG] Error sending TIME_REQ: {str(e)}")
            messagebox.showerror("Error", f"Error sending TIME_REQ: {str(e)}")
    
    def on_send_time_response(self, topic: str, payload: str) -> None:
        """Handle TIME_RESPONSE sending from observer"""
        try:
            print(f"[DEBUG] Sending TIME_RESPONSE via MQTT:")
            print(f"  Topic: {topic}")
            print(f"  Payload: {payload}")
            
            self.app.mqtt_manager.publish(topic, payload)
            print(f"[DEBUG] TIME_RESPONSE sent successfully")
            
            # Show in observer interface
            if self.app.current_view == AppView.OBSERVER:
                observer_view = self.app.views[AppView.OBSERVER]
                timestamp = format_timestamp()
                observer_view.add_sent_message(topic, payload, timestamp)
            
        except Exception as e:
            print(f"[DEBUG] Error sending TIME_RESPONSE: {str(e)}")
            messagebox.showerror("Error", f"Error sending TIME_RESPONSE: {str(e)}")


def create_app() -> ChronosPYApp:
    """
    Factory function to create the application.
    
    Returns:
        Configured application instance
    """
    root = tk.Tk()
    return ChronosPYApp(root) 