import simple_rf
import time

simple_rf.tx_setup()

while True:
    repeat = int(input("repeat = "))
    msg = "10101010" #input("Enter string of 8 bits:")
    for i in range(repeat):
        simple_rf.tx_send_msg(msg)
        time.sleep(0.01)
