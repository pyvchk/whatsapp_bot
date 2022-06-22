# whatsapp_bot
Programm for sending everyday massages to the target (group or person).

#
[config.ini]

You can change server and port for another mailbox

email/password - address from which you get QR_CODE's for authorization on your watsapp.web

to_addr - email in which you can get QR_CODE's

wa_target - target group or person name

wa_message - message

sending_time - time for sending message to target

#
Dockerfile for docker image build with command:

docker build -t {rep_name} {path/to/folder}
