import http.server
import requests
import qrcode
import base64
from io import BytesIO

class QRISHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # If the path is /qris, handle it
        if self.path.startswith('/qris'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Send a POST request to the external API
            api_url = "https://voteqrisbali.com/event/vote-donasi-buleleng-festival/vote/0198c29e-61f9-735d-a528-4f120a5fcc6a"
            response = requests.post(api_url)

            # Check if the response is successful
            if response.status_code == 200:
                # Get the data from the response
                data = response.json()

                # Assuming the response contains 'qr_string'
                qr_string = data.get("qr_string")
                
                if qr_string:
                    # Generate the QR code from the qr_string
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(qr_string)
                    qr.make(fit=True)

                    # Create an image from the QR code
                    img = qr.make_image(fill='black', back_color='white')

                    # Convert the image to base64
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    qr_image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                    # Generate the HTML to display the QR code
                    html = f"""
                    <html>
                        <head><title>QR Code Response</title></head>
                        <body>
                            <h2>QR Code Image:</h2>
                            <img src="data:image/png;base64,{qr_image_base64}" alt="QR Code">
                            <p>Press Space to reload the page</p>
                            <script>
                                // Event listener for Spacebar press to reload the page
                                window.addEventListener('keydown', function(event) {{
                                    if (event.key === " ") {{
                                        location.reload();  // Reload the page when Space is pressed
                                    }}
                                }});
                            </script>
                        </body>
                    </html>
                    """
                    # Send the HTML response back to the user
                    self.wfile.write(html.encode())
                else:
                    self.send_error(400, "No qr_string found in the API response.")
            else:
                self.send_error(400, "Failed to fetch data from the API.")
        else:
            self.send_error(404, "Not Found")

# Run the server
def run(server_class=http.server.HTTPServer, handler_class=QRISHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
