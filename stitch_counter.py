class Project:
    def __init__(self, name):
        self.name = name

class Yarn:
    def __init__(self):
        self.type = input("Which type of yarn would you like to use? ")

class Hook:
    def __init__(self, project):
        self.project = project



class Stitches:
    def __init__(self, project):
        self.project = project
        self.total = 0
        self.previous = 0
        self.last_added= 0

    def add_stitches(self):
        print(f"Previous total stitches: {self.total}")
        new = int(input("How many stitches did you just do? "))
        self.previous = self.total
        self.total += new
        self.last_added = new
        print(f"You added {new} stitches.")
        print(f"New total stitches: {self.total}")


       
    def show_stitches(self):
        print(f"Previous total: {self.previous}")
        print(f"Last added: {self.last_added}")
        print(f"Current total: {self.total}")