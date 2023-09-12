class config():
    def __init__(self):
        self.mariadb = {
                        'user' :"",
                        'password' : "",
                        'host' : "",
                        'port' : 'port_num',
                        'database' : ""
                        }
                        
        self.map_server_rack = {
            'rack_number' : ['ip', '', '', ''],
            '' : ['', '', '', ''],
            '' : ['', '', '', ''],
        }

        list_server = []
        for rack in self.map_server_rack:
            list_server += self.map_server_rack[rack]

        self.list_server = list_server
