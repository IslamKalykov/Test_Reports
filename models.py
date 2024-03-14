      
        
class Message:
    def __init__(self, date, sender_id, phone_number, service_center, sms_body, encoding, segments):
        self.date = date
        self.sender_id = sender_id
        self.phone_number = phone_number
        self.service_center = service_center
        self.sms_body = sms_body
        self.encoding = encoding
        self.segments = segments

    def __repr__(self):
        return f"Message(date={self.date}, sender_id={self.sender_id}, phone_number={self.phone_number}, service_center={self.service_center}, sms_body={self.sms_body}, encoding={self.encoding}, segments={self.segments})"

class Calls:
    def __init__(self) -> None:
        pass
