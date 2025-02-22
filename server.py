#!/usr/bin/env python3

import email
import http.server
import json
import threading
import urllib.parse
from email.parser import BytesParser
from email.policy import default
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO


class ControlServerHandler(BaseHTTPRequestHandler):

    def __init__(self, action_handlers, *args, **kwargs):
        self.actions = {}
        for action in ("up", "down", "left", "right", "full", "reset",
                       "manual"):
            self.actions[action] = action_handlers.get(action, None)
        super().__init__(*args, **kwargs)

    # Define action methods
    def on_up(self):
        print("Action: up")
        # Implement your 'up' action here

    def on_down(self):
        print("Action: down")
        # Implement your 'down' action here

    def on_left(self):
        print("Action: left")
        # Implement your 'left' action here

    def on_right(self):
        print("Action: right")
        # Implement your 'right' action here

    def on_full(self):
        print("Action: full")
        # Implement your 'full' action here

    def on_reset(self):
        print("Action: reset")
        # Implement your 'reset' action here

    def on_manual(self):
        print("Action: manual")
        # Implement your 'manual' action here

    def on_voice_cmd(self):
        # This method is handled in do_POST
        pass

    def on_exit(self):
        print("Action: exit - shutting down server.")
        # Respond to the client before shutting down
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'status': 'success', 'message': 'Server is shutting down.'}
        self.wfile.write(json.dumps(response).encode('utf-8'))
        # Shutdown the server in a separate thread to avoid blocking
        threading.Thread(target=self.server.shutdown).start()

    def do_GET(self):
        # Parse the URL path
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path in ['/', '/index.html']:
            # Serve the HTML page with buttons and AJAX functionality
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_content = self.generate_html()
            self.wfile.write(html_content.encode('utf-8'))
        elif path.startswith('/action/'):
            # Extract the action from the URL
            action = path.split('/action/')[1]
            # Map the action to the corresponding method
            action_method = getattr(self, f'on_{action}', None)
            if action_method and callable(action_method):
                action_method()
                # For 'exit', the response is already sent in the method
                if action != 'exit':
                    # Prepare a JSON response
                    response = {
                        'status': 'success',
                        'message': f'Action "{action}" executed successfully.'
                    }
                    response_bytes = json.dumps(response).encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Content-Length',
                                     str(len(response_bytes)))
                    self.end_headers()
                    self.wfile.write(response_bytes)
            else:
                # Action not found
                response = {
                    'status': 'error',
                    'message': f'Action "{action}" not found.'
                }
                response_bytes = json.dumps(response).encode('utf-8')
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Length', str(len(response_bytes)))
                self.end_headers()
                self.wfile.write(response_bytes)
        else:
            # Path not found
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Page not found.')

    def do_POST(self):
        # Handle POST requests for /action/voice_cmd
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/action/voice_cmd':
            # Parse the form data posted
            content_type = self.headers.get('Content-Type')
            if not content_type:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Content-Type header missing.')
                return

            # Parse multipart/form-data using the email module
            ctype, pdict = urllib.parse.parse_header(content_type)
            if ctype != 'multipart/form-data':
                self.send_response(400)
                self.end_headers()
                response = {
                    'status': 'error',
                    'message': 'Content-Type must be multipart/form-data.'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            boundary = pdict.get('boundary')
            if not boundary:
                self.send_response(400)
                self.end_headers()
                response = {
                    'status': 'error',
                    'message': 'Boundary not found in Content-Type.'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # Read the form data
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Parse the multipart data
            parser = BytesParser(policy=default)
            msg = parser.parsebytes(body)

            # Extract the audio file
            audio_data = None
            for part in msg.iter_parts():
                if part.get_content_disposition(
                ) == 'form-data' and part.get_param('name') == 'audio':
                    audio_data = part.get_payload(decode=True)
                    break

            if not audio_data:
                self.send_response(400)
                self.end_headers()
                response = {
                    'status': 'error',
                    'message': 'No audio data received.'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # Process the audio data to determine the command
            command = self.parse_voice_command(audio_data)

            if command and hasattr(self, f'on_{command}'):
                # Execute the corresponding action
                action_method = getattr(self, f'on_{command}')
                if callable(action_method):
                    action_method()
                    response = {
                        'status':
                        'success',
                        'message':
                        f'Voice command "{command}" executed successfully.'
                    }
                    self.send_response(200)
                else:
                    response = {
                        'status': 'error',
                        'message': f'Action "{command}" is not callable.'
                    }
                    self.send_response(400)
            else:
                # Unrecognized or missing command
                response = {
                    'status': 'error',
                    'message': f'Unrecognized voice command "{command}".'
                }
                self.send_response(400)

            # Send JSON response
            response_bytes = json.dumps(response).encode('utf-8')
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        else:
            # Path not found for POST
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Page not found.')

    def parse_voice_command(self, audio_data):
        """
        Placeholder function to parse audio data and extract the voice command.
        Implement this function using a speech recognition library or external API.
        """
        # Example: Using an external API or library to convert audio_data to text
        # For demonstration, we'll simulate this by returning a fixed command
        # In reality, you would process 'audio_data' to get the actual command
        print("Received audio data for voice command processing.")
        # TODO: Replace with actual audio processing
        # Example return value:
        # return "up"

        # Simulated command for demonstration purposes
        return "up"  # Replace with actual parsed command

    def log_message(self, format, *args):
        # Override to disable console logging
        return

    def generate_html(self):
        # Define the buttons in the specified 3x3 grid layout
        buttons = [
            ('重置', '/action/reset'),
            ('Y前进', '/action/up'),
            ('退出', '/action/exit'),
            ('X后退', '/action/left'),
            ('洁净', '/action/full'),
            ('X前进', '/action/right'),
            ('手动', '/action/manual'),
            ('Y后退', '/action/down'),
            ('语音', '/action/voice_cmd')  # Voice Command button
        ]

        # Arrange buttons in the desired grid layout
        grid_positions = [
            buttons[0],  # Reset
            buttons[1],  # Up
            buttons[2],  # Exit
            buttons[3],  # Left
            buttons[4],  # Full
            buttons[5],  # Right
            buttons[6],  # Manual
            buttons[7],  # Down
            buttons[8]  # Voice
        ]

        # Generate HTML buttons with unique IDs
        html_buttons = ""
        for button in grid_positions:
            label, endpoint = button
            if label.lower() == 'voice':
                # Special handling for Voice Command button
                html_buttons += f"""
                <div class="grid-item">
                    <button id="btn-{label.lower()}">{label}</button>
                </div>
                """
            else:
                html_buttons += f"""
                <div class="grid-item">
                    <button id="btn-{label.lower()}" data-endpoint="{endpoint}">{label}</button>
                </div>
                """

        # Complete HTML page with JavaScript for AJAX and Voice Command
        html_page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>超级无敌控制面板</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin-top: 50px;
                }}
                .grid-container {{
                    display: grid;
                    grid-template-columns: repeat(3, 120px);
                    grid-gap: 20px;
                    justify-content: center;
                    margin-bottom: 30px;
                }}
                .grid-item {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                button {{
                    padding: 20px;
                    font-size: 16px;
                    width: 120px;
                    height: 120px;
                    cursor: pointer;
                }}
                #response {{
                    font-size: 18px;
                    color: #333;
                }}
            </style>
        </head>
        <body>
            <h1>超级无敌控制面板</h1>
            <div class="grid-container">
                {html_buttons}
            </div>
            <div id="response">无操作</div>

            <script>
                // Function to handle button clicks for standard actions
                function handleButtonClick(event) {{
                    const button = event.target;
                    const endpoint = button.getAttribute('data-endpoint');
                    if (!endpoint) return;

                    fetch(endpoint)
                        .then(response => response.json())
                        .then(data => {{
                            if (data.status === 'success') {{
                                document.getElementById('response').innerText = data.message;
                            }} else {{
                                document.getElementById('response').innerText = 'Error: ' + data.message;
                            }}
                        }})
                        .catch(error => {{
                            document.getElementById('response').innerText = 'Fetch error: ' + error;
                        }});
                }}

                // Attach event listeners to all standard buttons except 'Voice'
                document.querySelectorAll('button').forEach(button => {{
                    if (button.id !== 'btn-voice') {{
                        button.addEventListener('click', handleButtonClick);
                    }}
                }});

                // Voice Command Button Handling
                const voiceCmdButton = document.getElementById('btn-voice');
                let mediaRecorder;
                let audioChunks = [];

                voiceCmdButton.addEventListener('click', () => {{
                    // Check for microphone access
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                        alert('Microphone API not supported in this browser.');
                        return;
                    }}

                    // Request microphone access
                    navigator.mediaDevices.getUserMedia({{ audio: true }})
                        .then(stream => {{
                            mediaRecorder = new MediaRecorder(stream);
                            mediaRecorder.start();

                            // Collect audio data
                            mediaRecorder.addEventListener('dataavailable', event => {{
                                audioChunks.push(event.data);
                            }});

                            // Stop recording after 1 second
                            mediaRecorder.addEventListener('stop', () => {{
                                const audioBlob = new Blob(audioChunks, {{ 'type' : 'audio/webm; codecs=opus' }});
                                audioChunks = []; // Reset for next recording

                                // Prepare form data
                                const formData = new FormData();
                                formData.append('audio', audioBlob, 'voice_cmd.webm');

                                // Send audio data to the server
                                fetch('/action/voice_cmd', {{
                                    method: 'POST',
                                    body: formData
                                }})
                                .then(response => response.json())
                                .then(data => {{
                                    if (data.status === 'success') {{
                                        document.getElementById('response').innerText = data.message;
                                    }} else {{
                                        document.getElementById('response').innerText = 'Error: ' + data.message;
                                    }}
                                }})
                                .catch(error => {{
                                    document.getElementById('response').innerText = 'Fetch error: ' + error;
                                }});
                            }});

                            // Stop recording after 1 second
                            setTimeout(() => {{
                                mediaRecorder.stop();
                                stream.getTracks().forEach(track => track.stop());
                            }}, 1000);
                        }})
                        .catch(err => {{
                            alert('Microphone access denied.');
                            console.error(err);
                        }});
                }});
            </script>
        </body>
        </html>
        """
        return html_page


if __name__ == '__main__':
    port = 8000
    server_address = ('0.0.0.0', port)
    handler_class = partial(ControlServerHandler, {})
    httpd = HTTPServer(server_address, handler_class)
    print(f"Server running on http://0.0.0.0:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server.")
        httpd.server_close()
