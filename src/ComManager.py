import threading
import zmq 
import time 
import time
import threading 
import sys 
import os
import pysftp
import fnmatch
from dotenv import load_dotenv

load_dotenv()

hostname = os.getenv('HOSTNAME')
username = os.getenv('USER')
password = os.getenv("PASSWORD")

class SftpManager:
    def __init__(self):
        pass

    def sftp_upload_dbc(self, dbc_path):
        with pysftp.Connection(host=hostname, username=username, password=password, port=22) as sftp:
            sftp.put(dbc_path, './dbc.dbc', confirm=True)

    def sftp_upload_dbc_thread(self, dbc_path):
        thread = threading.Thread(target=self.sftp_upload_dbc, args=(dbc_path,))
        thread.daemon = True 
        thread.start()

    def sftp_download_logfiles(self):
        remote_directory = '.'
        file_pattern = f'{hostname}_*'
        local_directory = os.getcwd()
        with pysftp.Connection(host=hostname, username=username, password=password, port=22) as sftp:
            remote_files = sftp.listdir(remote_directory)
            while fnmatch.filter(remote_files, '*.csv') == []:
                remote_files = sftp.listdir(remote_directory)
            for remote_file in fnmatch.filter(remote_files, file_pattern):
                remote_file_path = f'{remote_directory}/{remote_file}'
                local_file_path = f'{local_directory}/{remote_file}'
                sftp.get(remote_file_path, local_file_path)

class TcpManager:
    def __init__(self):
        self.configure_sockets()

    def configure_sockets(self):
        self.context = zmq.Context()
        self.pub_socket = self.context.socket(zmq.PUB)
        self.router_socket = self.context.socket(zmq.ROUTER)
        try:
            self.pub_socket.bind('tcp://*:5558')
            self.router_socket.bind('tcp://*:5559')
        except Exception as e:
            sys.exit()

    def request_until_ack(self, topic, message):
        received = False
        while not received:
            try:
                self.pub_socket.send_multipart([topic.encode(), message.encode()])
            except Exception as e:
                print(f'Error sending message: {e}')
            try:
                address, id, message = self.router_socket.recv_multipart(zmq.DONTWAIT)
                received = True 
            except zmq.Again:
                pass
            time.sleep(1)
        return address, id, message

    def identify_request(self, device_dict, label):
        label.set('Waiting for response...')
        topic = 'identify'
        message = 'requested'
        address, id, message = self.request_until_ack(topic, message)
        device_name = message.decode().split()[0]
        response = f'{device_name} - connected - {device_dict[device_name]}'
        label.set(response)

    def start_request(self, message_queue, stop_event):
        id_list = []
        topic = 'start'
        message = 'requested'
        address, id, message = self.request_until_ack(topic, message)
        while not stop_event.is_set():
            try:
                address, id, message = self.router_socket.recv_multipart(zmq.DONTWAIT)
                if int(id.decode()) >= 0:
                    if id not in id_list:
                        message_queue.put(message.decode())
                        id_list.append(id)
            except zmq.Again:
                pass

    def stop_request(self):
        self.request_until_ack('stop', 'requested')

    def clean_request(self):
        self.request_until_ack('clean', 'requested')

    def cleanup(self):
        self.pub_socket.close()
        self.router_socket.close()
        self.context.term()

class RequestThreader:
    def __init__(self):
        pass

    def thread_function(self, target, args=None): 
        if args is None:
            data_flow_thread = threading.Thread(target=target)
        else:
            data_flow_thread = threading.Thread(target=target, args=args)
        data_flow_thread.daemon = True 
        data_flow_thread.start()
        return data_flow_thread
    
    def identify_request(self, device_dict, label):
        self.tcpmanager = TcpManager()
        self.tcpmanager.identify_request(device_dict, label)
        self.tcpmanager.cleanup()

    def start_request(self, message_queue, stop_event):
        self.tcpmanager = TcpManager()
        self.tcpmanager.start_request(message_queue, stop_event)
        self.tcpmanager.cleanup()

    def stop_request(self):
        self.sftpmanager = SftpManager()
        self.tcpmanager = TcpManager()
        self.tcpmanager.stop_request()
        self.sftpmanager.sftp_download_logfiles()
        self.tcpmanager.clean_request()
        self.tcpmanager.cleanup()

    def clean_request(self):
        self.sftpmanager = SftpManager()
        self.tcpmanager = TcpManager()
        self.sftpmanager.sftp_download_logfiles()
        self.tcpmanager.clean_request()
        self.tcpmanager.cleanup()

    def thread_identify_request(self, device_dict, label):
        thread = self.thread_function(self.identify_request, (device_dict, label))

    def thread_start_request(self, message_queue, stop_event):
        thread = self.thread_function(self.start_request, (message_queue, stop_event))

    def thread_stop_request(self):
        thread = self.thread_function(self.stop_request)

    def thread_clean_request(self):
        thread = self.thread_function(self.clean_request)
