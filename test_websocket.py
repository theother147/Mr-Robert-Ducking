import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = "ws://localhost:8765"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Type your message (or 'quit' to exit)")
            print("Sending test message...")
            
            # Example test message
            message = {
                "message": "Can you help me understand this code?",
                "files": [{
                    "filename": "test.py",
                    "content": "def hello():\n    print('Hello World!')"
                }]
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            print("\nMessage sent! Waiting for response...")
            
            # Get the response
            response = await websocket.recv()
            print(f"\nReceived response:\n{json.dumps(json.loads(response), indent=2)}")
            
            # Interactive mode
            while True:
                try:
                    # Get user input
                    user_message = input("\nEnter your message (or 'quit' to exit): ")
                    if user_message.lower() == 'quit':
                        break
                        
                    # Create message with optional file content
                    message = {
                        "message": user_message,
                        "files": [{
                            "filename": "test.py",
                            "content": "# Your code here"
                        }]
                    }
                    
                    # Send message
                    await websocket.send(json.dumps(message))
                    print("Message sent! Waiting for response...")
                    
                    # Get response
                    response = await websocket.recv()
                    print(f"\nReceived response:\n{json.dumps(json.loads(response), indent=2)}")
                    
                except KeyboardInterrupt:
                    break
                    
    except websockets.exceptions.ConnectionClosed:
        print("\nConnection closed by server")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\nTest client stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        print("\nConnection closed") 