import os
from ..app.main import Controller


class RemoteDriveController(Controller):
    def __init__(self):
        super().__init__()
        
        with open(os.path.join(__file__, "remote_drive_code.py"), "r") as f:
            self.code = f.read()
        


if __name__ == "__main__":
    controller = RemoteDriveController()
    controller.main()