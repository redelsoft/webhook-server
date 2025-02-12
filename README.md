I created this small Python webhook server to analyze and/or test API calls from external systems.
It receives JSON payload and prints it to the screen. The http headers are also printed to the screen.

The bearer token are stored in a local txt file token.txt. The username/password combinations are
stored in the credentials.txt file.

In the following example screenshots the webhook traffic is routed through a NGINX reverse proxy,
since I didn't want to directly connect the webhook server to the Internet

![image](https://github.com/user-attachments/assets/a0788516-2149-467c-ab6a-3f9c210734dd)

![image](https://github.com/user-attachments/assets/207bf179-0ef8-45ab-b674-819adf9a8db0)

Standard disclaimer:
This server is for testing / debugging purposes only. Feel free to further develop it.
USE AT YOUR OWN RISK!
