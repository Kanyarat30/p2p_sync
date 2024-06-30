#ส่วนนี้เป็นการ import โมดูลที่จำเป็น
import socket   #ใช้สำหรับการสื่อสารผ่านเครือข่าย
import threading    #ใช้สำหรับการทำงานแบบหลาย thread
import json     #ใช้สำหรับการแปลงข้อมูลเป็น JSON และกลับกัน
import sys      #ใช้สำหรับการเข้าถึงตัวแปรและฟังก์ชันที่เกี่ยวข้องกับ Python interpreter
import os       #ใช้สำหรับการทำงานกับระบบปฏิบัติการ
import secrets  #ใช้สำหรับการสร้างข้อมูลที่ปลอดภัยทางคริปโตกราฟี


#class หลักของโปรแกรม ชื่อ Node
class Node:
    def __init__(self, host, port): #__init__ เป็น constructor ที่รับ host และ port
        self.host = host    #เป็นตัวแปรที่เก็บค่า IP address หรือชื่อโฮสต์ที่โหนดนี้จะใช้ในการรับการเชื่อมต่อ
        self.port = port    #เป็นตัวแปรที่เก็บหมายเลขพอร์ตที่โหนดนี้จะใช้ในการรับการเชื่อมต่อ
        self.peers = []  # เก็บรายการ socket ของ peer ที่เชื่อมต่อ
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #สร้าง socket object สำหรับโหนดนี้
        #socket.AF_INET: ระบุว่าใช้ IPv4 สำหรับการสื่อสาร
        #socket.SOCK_STREAM: ระบุว่าใช้โปรโตคอล TCP ซึ่งเป็นการเชื่อมต่อแบบ reliable, ordered, และ error-checked
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   #ตั้งค่าตัวเลือกสำหรับ socket
        self.transactions = []  # เก็บรายการ transactions
        self.transaction_file = f"transactions_{port}.json"  # ไฟล์สำหรับบันทึก transactions
        self.wallet_address = self.generate_wallet_address()  # สร้าง wallet address สำหรับโหนดนี้

    def generate_wallet_address(self):
        # สร้าง wallet address แบบง่ายๆ (ในระบบจริงจะซับซ้อนกว่านี้มาก)
        return '0x' + secrets.token_hex(20)
        #ฟังก์ชันนี้สร้าง wallet address แบบง่ายๆ โดยใช้ secrets.token_hex(20) เพื่อสร้างสตริงแบบสุ่มที่ปลอดภัย

    def start(self):
        # เริ่มต้นการทำงานของโหนด
        self.socket.bind((self.host, self.port))    #ผูก (bind) socket กับ host และ port ที่กำหนดไว้ การ bind นี้ทำให้โหนดพร้อมรับการเชื่อมต่อที่ address และ port ที่กำหนด
        self.socket.listen(1)   #เริ่มการรับฟังการเชื่อมต่อที่เข้ามา ตัวเลข 1 หมายถึงจำนวนการเชื่อมต่อที่รอในคิวได้ (backlog)ในที่นี้กำหนดเป็น 1 ซึ่งหมายถึงรับได้ทีละ 1 การเชื่อมต่อ
        print(f"Node listening on {self.host}:{self.port}") #แสดงข้อความว่าโหนดกำลังรับฟังการเชื่อมต่อที่ host และ port ใด (ช่วยให้ผู้ใช้ทราบว่าโหนดพร้อมทำงานแล้ว)
        print(f"Your wallet address is: {self.wallet_address}") #แสดง wallet address ของโหนดนี้ (ช่วยให้ผู้ใช้ทราบ wallet address ของตนเอง)

        self.load_transactions()  # โหลด transactions จากไฟล์ (ถ้ามี) ทำให้โหนดมีข้อมูล transactions ที่เคยบันทึกไว้ก่อนหน้านี้

        # เริ่ม thread สำหรับรับการเชื่อมต่อใหม่
        accept_thread = threading.Thread(target=self.accept_connections)    #การใช้ thread แยกนี้ทำให้โหนดสามารถรับการเชื่อมต่อใหม่ได้ตลอดเวลา โดยไม่ block การทำงานอื่น
        accept_thread.start()   #เริ่มการทำงานของ thread ที่สร้างไว้ thread นี้จะคอยรับการเชื่อมต่อใหม่ที่เข้ามาตลอดเวลา

    #ฟังก์ชันนี้ทำงานในลูปไม่สิ้นสุด รอรับการเชื่อมต่อใหม่ และเริ่ม thread ใหม่สำหรับจัดการแต่ละการเชื่อมต่อ
    def accept_connections(self):   #ฟังก์ชันนี้ทำหน้าที่รับการเชื่อมต่อใหม่ที่เข้ามายังโหนด
        while True: #ทำให้โหนดคอยรับการเชื่อมต่อใหม่ตลอดเวลาโดยไม่หยุด
            # รอรับการเชื่อมต่อใหม่
            client_socket, address = self.socket.accept()   #self.socket.accept() เป็นคำสั่งที่รอรับการเชื่อมต่อใหม่ (blocking call)
            #เมื่อมีการเชื่อมต่อเข้ามา จะได้รับclient_socket คือ socket object สำหรับการสื่อสารกับ client ที่เชื่อมต่อเข้ามา และ address คือ tuple ที่ประกอบด้วย IP address และ port ของ client ที่เชื่อมต่อเข้ามา
            print(f"New connection from {address}") #{address} จะแสดง IP address และ port ของ client ที่เชื่อมต่อเข้ามา

            # เริ่ม thread ใหม่สำหรับจัดการการเชื่อมต่อนี้
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,)) #target=self.handle_client: กำหนดให้ thread นี้ทำงานฟังก์ชัน handle_client
            #args=(client_socket,): ส่ง client_socket เป็นอาร์กิวเมนต์ให้ฟังก์ชัน handle_client การใช้ thread แยกนี้ทำให้สามารถรองรับการเชื่อมต่อหลายๆ คนพร้อมกันได้
            client_thread.start() #ทำให้เริ่มกระบวนการจัดการ client รายใหม่นี้ในอีก thread หนึ่ง

    #ประกาศฟังก์ชัน handle_client ซึ่งเป็นเมธอดของคลาส Node
    def handle_client(self, client_socket): #รับพารามิเตอร์ client_socket ซึ่งเป็น socket object สำหรับการสื่อสารกับ client ที่เชื่อมต่อเข้ามา
        while True: #เริ่มลูปแบบไม่สิ้นสุด เพื่อรับข้อมูลจาก client ตลอดเวลา
            try:
                # รับข้อมูลจาก client ผ่าน socket
                data = client_socket.recv(1024) # 1024 คือขนาดบัฟเฟอร์ในไบต์ที่จะใช้รับข้อมูล
                if not data:    #ตรวจสอบว่าได้รับข้อมูลหรือไม่ ถ้าไม่มีข้อมูล (เช่น client ปิดการเชื่อมต่อ) จะออกจากลูป
                    break
                message = json.loads(data.decode('utf-8'))  #แปลงข้อมูลที่ได้รับ (ซึ่งเป็นไบต์) เป็นสตริง UTF-8 และ แปลงสตริง JSON เป็น Python object ด้วย json.loads()
                
                self.process_message(message, client_socket) #เรียกฟังก์ชัน process_message เพื่อประมวลผลข้อความที่ได้รับ ส่งข้อความและ socket ของ client ไปยังฟังก์ชันนี้

            except Exception as e:  #จับข้อผิดพลาดทั้งหมดที่อาจเกิดขึ้นในบล็อก try
                print(f"Error handling client: {e}")    #แสดงข้อความแจ้งเตือนเมื่อเกิดข้อผิดพลาด
                break   #ออกจากลูป while เมื่อเกิดข้อผิดพลาด

        client_socket.close() #ปิดการเชื่อมต่อ socket กับ client หลังจากออกจากลูป

    #ประกาศฟังก์ชัน connect_to_peer ซึ่งเป็นเมธอดของคลาส Node
    def connect_to_peer(self, peer_host, peer_port):    #รับพารามิเตอร์ peer_host (IP หรือโฮสต์เนมของ peer) และ peer_port (พอร์ตของ peer)
        try:    #เริ่มบล็อก try-except เพื่อจัดการข้อผิดพลาดที่อาจเกิดขึ้นระหว่างการเชื่อมต่อ
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # สร้าง socket ใหม่สำหรับการเชื่อมต่อกับ peer
            peer_socket.connect((peer_host, peer_port)) #พยายามเชื่อมต่อไปยัง peer ที่ระบุ ถ้าการเชื่อมต่อสำเร็จ จะดำเนินการต่อ ถ้าไม่สำเร็จจะเกิด exception
            self.peers.append(peer_socket) #เพิ่ม socket ที่เชื่อมต่อสำเร็จแล้วเข้าไปในรายการ peers ของโหนด
            print(f"Connected to peer {peer_host}:{peer_port}") #แสดงข้อความยืนยันว่าเชื่อมต่อกับ peer สำเร็จแล้ว

            # ขอข้อมูล transactions ทั้งหมดจาก peer ที่เชื่อมต่อ
            self.request_sync(peer_socket)

            # เริ่ม thread สำหรับรับข้อมูลจาก peer นี้
            peer_thread = threading.Thread(target=self.handle_client, args=(peer_socket,))
            peer_thread.start() #ทำให้เริ่มกระบวนการรับและส่งข้อมูลกับ peer ในอีก thread หนึ่ง

        except Exception as e:  #จับข้อผิดพลาดทั้งหมดที่อาจเกิดขึ้นในระหว่างการเชื่อมต่อหรือการตั้งค่า
            print(f"Error connecting to peer: {e}") #แสดงข้อความแจ้งเตือนเมื่อเกิดข้อผิดพลาดในการเชื่อมต่อ

    def broadcast(self, message): #ประกาศฟังก์ชัน broadcast ซึ่งเป็นเมธอดของคลาส Node
        # ส่งข้อมูลไปยังทุก peer ที่เชื่อมต่ออยู่
        for peer_socket in self.peers:  #เริ่มลูปที่จะวนผ่านทุก socket ในรายการ self.peers ซี่ง self.peers เป็นลิสต์ที่เก็บ socket ของทุก peer ที่เชื่อมต่ออยู่
            try:    #เริ่มบล็อก try-except เพื่อจัดการข้อผิดพลาดที่อาจเกิดขึ้นระหว่างการส่งข้อความ
                peer_socket.send(json.dumps(message).encode('utf-8')) #json.dumps(message): แปลง Python object (message) เป็นสตริง JSON
                #.encode('utf-8'): แปลงสตริง JSON เป็นไบต์ใน UTF-8 encoding
                #peer_socket.send(...): ส่งข้อมูลที่แปลงแล้วไปยัง peer ผ่าน socket
            except Exception as e: #จับข้อผิดพลาดทั้งหมดที่อาจเกิดขึ้นในระหว่างการส่งข้อความ
                print(f"Error broadcasting to peer: {e}") #แสดงข้อความแจ้งเตือนเมื่อเกิดข้อผิดพลาดในการส่งข้อความ
                self.peers.remove(peer_socket) #ลบ socket ของ peer ที่เกิดข้อผิดพลาดออกจากรายการ self.peers เพื่อไม่ให้พยายามส่งข้อความไปยัง peer ที่ไม่สามารถเชื่อมต่อได้อีก

    def process_message(self, message, client_socket): #ประกาศฟังก์ชัน process_message ซึ่งเป็นเมธอดของคลาส Node
        # ประมวลผลข้อความที่ได้รับ
        if message['type'] == 'transaction': #ตรวจสอบว่าประเภทของข้อความเป็น 'transaction' หรือไม่
            print(f"Received transaction: {message['data']}") #แสดงข้อมูลของ transaction ที่ได้รับ message['data'] คือข้อมูลของ transaction
            self.add_transaction(message['data']) #เรียกฟังก์ชัน add_transaction เพื่อเพิ่ม transaction ใหม่เข้าสู่ระบบ
        elif message['type'] == 'sync_request': #ตรวจสอบว่าประเภทของข้อความเป็น 'sync_request' หรือไม่ ใช้สำหรับจัดการคำขอซิงโครไนซ์ข้อมูลจาก peer อื่น
            self.send_all_transactions(client_socket) #เรียกฟังก์ชัน send_all_transactions เพื่อส่ง transactions ทั้งหมดไปยัง peer ที่ขอ
        elif message['type'] == 'sync_response': #ตรวจสอบว่าประเภทของข้อความเป็น 'sync_response' หรือไม่ ใช้สำหรับจัดการการตอบกลับของคำขอซิงโครไนซ์
            self.receive_sync_data(message['data']) #เรียกฟังก์ชัน receive_sync_data เพื่อประมวลผลข้อมูลที่ได้รับจากการซิงโครไนซ์
        else:
            print(f"Received message: {message}") #แสดงข้อความทั้งหมดที่ได้รับ ในกรณีที่ไม่ตรงกับประเภทที่กำหนดไว้

    def add_transaction(self, transaction): #ประกาศฟังก์ชัน add_transaction ซึ่งเป็นเมธอดของคลาส Node
        # เพิ่ม transaction ใหม่และบันทึกลงไฟล์
        if transaction not in self.transactions: #ตรวจสอบว่าธุรกรรมนี้ยังไม่มีอยู่ในรายการ self.transactions เป็นลิสต์ที่เก็บธุรกรรมทั้งหมดของโหนด การตรวจสอบนี้ช่วยป้องกันการเพิ่มธุรกรรมซ้ำ
            self.transactions.append(transaction) #ถ้าธุรกรรมไม่ซ้ำ จะถูกเพิ่มเข้าไปในรายการ self.transactions
            self.save_transactions() #บันทึกรายการธุรกรรมทั้งหมดลงในไฟล์
            print(f"Transaction added and saved: {transaction}") #แสดงข้อความยืนยันว่าธุรกรรมได้ถูกเพิ่มและบันทึกเรียบร้อยแล้ว

    def create_transaction(self, recipient, amount): #ประกาศฟังก์ชัน create_transaction ซึ่งเป็นเมธอดของคลาส Node
        # สร้าง transaction ใหม่
        transaction = {
            'sender': self.wallet_address, #ที่อยู่กระเป๋าเงินของผู้ส่ง (โหนดปัจจุบัน)
            'recipient': recipient, #ที่อยู่กระเป๋าเงินของผู้รับ (ที่ได้รับเป็นพารามิเตอร์)
            'amount': amount #จำนวนเงินที่ส่ง (ที่ได้รับเป็นพารามิเตอร์)
        }
        self.add_transaction(transaction) #เพิ่มธุรกรรมเข้าไปในรายการธุรกรรมของโหนดและบันทึกลงไฟล์
        self.broadcast({'type': 'transaction', 'data': transaction}) #ส่งข้อมูลธุรกรรมไปยังทุกโหนดที่เชื่อมต่ออยู่ในเครือข่าย
        #'type': 'transaction' - ระบุว่าเป็นข้อความประเภทธุรกรรม
        #'data': transaction - ข้อมูลของธุรกรรมที่สร้างขึ้น

    def save_transactions(self):
        # บันทึก transactions ลงไฟล์
        with open(self.transaction_file, 'w') as f: #เปิดไฟล์ที่มีชื่อตามค่าใน self.transaction_file ในโหมดเขียน ('w')
            json.dump(self.transactions, f) #ใช้ฟังก์ชัน json.dump() เพื่อแปลงข้อมูลในรายการ self.transactions เป็นรูปแบบ JSON และเขียนลงในไฟล์

    def load_transactions(self):
        # โหลด transactions จากไฟล์ (ถ้ามี)
        if os.path.exists(self.transaction_file):   #ตรวจสอบว่าไฟล์ที่มีชื่อตาม self.transaction_file มีอยู่จริงหรือไม่
            with open(self.transaction_file, 'r') as f: #ถ้าไฟล์มีอยู่ จะเปิดไฟล์ในโหมดอ่าน ('r')
                self.transactions = json.load(f)    #ใช้ฟังก์ชัน json.load() เพื่ออ่านข้อมูล JSON จากไฟล์และแปลงเป็นโครงสร้างข้อมูลของ Python
            print(f"Loaded {len(self.transactions)} transactions from file.")   #แสดงข้อความยืนยันว่าได้โหลดธุรกรรมจากไฟล์เรียบร้อยแล้ว len(self.transactions) จะแสดงจำนวนธุรกรรมที่โหลดมา

    def request_sync(self, peer_socket):
        # ส่งคำขอซิงโครไนซ์ไปยัง peer
        sync_request = json.dumps({"type": "sync_request"}).encode('utf-8')
        peer_socket.send(sync_request) #ใช้เมธอด send ของ peer_socket เพื่อส่งข้อมูลในตัวแปร sync_request ไปยัง peer

    def send_all_transactions(self, client_socket):
        # ส่ง transactions ทั้งหมดไปยังโหนดที่ขอซิงโครไนซ์
        sync_data = json.dumps({
            "type": "sync_response", #มีค่าเป็น "sync_response" เพื่อระบุว่านี่เป็นการตอบกลับการซิงโครไนซ์
            "data": self.transactions   #มีค่าเป็น self.transactions ซึ่งเป็นลิสต์ของธุรกรรมทั้งหมดที่เก็บอยู่ในโหนดนี้
        }).encode('utf-8')  #แปลงสตริง JSON เป็นไบต์ในรูปแบบ UTF-8 encoding
        client_socket.send(sync_data)   #ผลลัพธ์ทั้งหมดถูกเก็บในตัวแปร sync_data

    def receive_sync_data(self, sync_transactions):
        # รับและประมวลผลข้อมูล transactions ที่ได้รับจากการซิงโครไนซ์
        for tx in sync_transactions:    #เริ่มลูป for ที่วนผ่านทุกธุรกรรม (tx) ในลิสต์ sync_transactions
            self.add_transaction(tx)    #เพิ่มธุรกรรมเข้าไปในรายการธุรกรรมของโหนดปัจจุบัน (ถ้ายังไม่มีอยู่) และบันทึกลงไฟล์
        print(f"Synchronized {len(sync_transactions)} transactions.")   #หลังจากเพิ่มธุรกรรมทั้งหมดแล้ว, แสดงข้อความยืนยันว่าได้ซิงโครไนซ์ธุรกรรมเสร็จสิ้น

if __name__ == "__main__":  #นี่เป็นการตรวจสอบว่าสคริปต์นี้กำลังถูกรันโดยตรงหรือไม่ (ไม่ได้ถูก import เป็นโมดูล)
    if len(sys.argv) != 2:  #ตรวจสอบว่ามีการระบุพอร์ตเมื่อรันสคริปต์หรือไม่
        print("Usage: python script.py <port>") #ถ้าไม่มี จะแสดงข้อความวิธีใช้และจบโปรแกรมด้วยสถานะผิดพลาด
        sys.exit(1)
    
    port = int(sys.argv[1]) #แปลงพอร์ตเป็นตัวเลข
    node = Node("0.0.0.0", port)  # ใช้ "0.0.0.0" เพื่อรับการเชื่อมต่อจากภายนอก
    node.start()    #เริ่มการทำงานของโหนด
    
    while True:
        print("\n1. Connect to a peer")
        print("2. Create a transaction")
        print("3. View all transactions")
        print("4. View my wallet address")
        print("5. Exit")
        choice = input("Enter your choice: ")
        
        if choice == '1':   # เชื่อมต่อกับ peer
            peer_host = input("Enter peer host to connect: ")
            peer_port = int(input("Enter peer port to connect: "))
            node.connect_to_peer(peer_host, peer_port)
        elif choice == '2': # สร้างธุรกรรมใหม่
            recipient = input("Enter recipient wallet address: ")
            amount = float(input("Enter amount: "))
            node.create_transaction(recipient, amount)
        elif choice == '3': # แสดงธุรกรรมทั้งหมด
            print("All transactions:")
            for tx in node.transactions:
                print(tx)
        elif choice == '4': #แสดง wallet address
            print(f"Your wallet address is: {node.wallet_address}")
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")  #ถ้าเลือกตัวเลือกที่ไม่มี จะแสดงข้อความแจ้งเตือน

    print("Exiting...") #แสดงข้อความเมื่อออกจากโปรแกรม