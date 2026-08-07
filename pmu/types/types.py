class CourseIdentifier: 
    def __init__(self, course_num: int, reunion_num: int, programme: str):
        self.course_num = course_num
        self.reunion_num = reunion_num
        self.programme = programme
    
    def __init__(self, course_id: str):
        self.course_num = int(course_id.split('/')[-1].split('C')[1])
        self.reunion_num = int(course_id.split('/')[-2].split('R')[1])
        self.programme = course_id.split('/')[0]

    def __str__(self) -> str:
        return f"{self.programme}/R{self.reunion_num}/C{self.course_num}"

class ReunionIdentifier:
    def __init__(self, reunion_num: int, programme: str):
        self.reunion_num = reunion_num
        self.programme = programme

    def __str__(self) -> str:
        return f"{self.programme}/R{self.reunion_num}"

class ProgrammeIdentifier:
    def __init__(self, programme: str):
        self.programme = programme

    def __str__(self) -> str:
        return self.programme