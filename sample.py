#!/usr/bin/env python3

import rospy
import smach
import smach_ros
from subprocess import call, Popen
from openai import OpenAI
# from dotenv import load_dotenv
#import gpsr_humancheck as human
import os
#import gpsr_objectcount as objectcount

# load_dotenv()
client = OpenAI()

sccnt = 0
cmd = "None"
flow = []
obj_pos = []
obj_tf = []
ans = ""
change_cnt = 1
count = 0
request = ""
inspection_ps = [1.0105649748660985, 0.060181374302244434, -0.0027471574721059065]
answer = ""
record = ""
LLMinput = ""
ROBOT_SKILLS = ["Image-recognition", "Speech-Synthesis", "Speech-Recognition", "Object-Grasping", "Movement"]
room =['hallway', 'living-room', 'dining-room']
PLACE = {"chair-A": [1.8570564717153717, 3.307250260111791, 3.0958225673170516], "chair-B": [1.8468843765484404, 4.085534572868467, 3.1241833105427705], "long-table-A": [2.5656691266350276, -0.03782429456527259, -1.6481339386353668], "long-table-B": [2.2103222169610026, 1.6031824794420644, 1.549648026590653], "shelf": [3.024514139817899, 4.134627199017964, 1.6072535224873283], "tall-table": [1.0427735739662425, 1.6650659761375122, 1.5345697035279628], "bin-A": [3.5092018167374377, -0.24300070247420438, -1.648805255808813], "bin-B": [4.049962192668305, -0.24778627011570886, -1.584708083515467], "drawer": [1.2425879887964395, 0.2176427722430392, -1.649288505191652]}
ROOM = {"hallway": [0.8890899034799168, -0.15938533257163473, 0.6589883334190397], "living-room": [2.611189983538178, -0.23748243998677726, 0.8901750735540216], "dining-room": [4.06030003638313, 3.216393077771914, 2.3711358002213614]}
PERSONNAME = ["Amelia", "Angel", "Charlie", "Ava", "Hunter", "Jack", "Charlotte", "Max", "Noah", "Oliver", "Mia", "Paker", "Sam", "Thomas", "William"]
OBJLIST = {1:"water", 2:"milk tea", 3:"biscuits", 4:"corn_soup", 5:"apple", 6:"lemon", 7:"bowl", 8:"mug"}
CLASSLIST = {"drink":["water", "milk tea"], "food":["biscuits", "corn soup"], "fruits":["apple", "lemon"], "dishware":["bowl", "mug"]}
POSELIST = ["standing", "raising one hand", "waving both hands over head", "performing the thumbs up symbol", "sitting on a chair"]

LLMprompt = """You are a technician giving commands to a home-working robot. The robot can execute commands (functions) for "Command-Question" "Movement" "Object-Grasping" "Put" "Humancount" "Objectcount" "Speech-Synthesis" "Findperson" "Question" "Get-Closeperson" "Ask" "Recoding-Speech" and "Finish" Each function has a meaning, arguments and specific gravity (specific gravity is frequency of use. 100 is good but 50 is bat):
- Command-Question: Meaning is the "Ask questions about what is unclear about the command.". Argument is the "Questions to ask". specific gravity is 50.
- Movement: Meaning is the "Move to target location". Argument is the "location name" or "room name". specific gravity is 90.
- Object-Grasping: Meaning is the "Grab an object.". Argument is the "object name". specific gravity is 90.
- Put: Meaning is the "Put down what the robot is grabbing.". Argument is Null. specific gravity is 90.
- Humancount: Meaning is the "Count the number of people who can see the robot". Argument is Null. specific gravity is 90.
- Objectcount: Meaning is the "Counts the number of specified objects visible to the robot". Argument is the "object name". specific gravity is 90.
- Speech-Synthesis:  Meaning is the "Speaks up for the specified content". Argument is the "spoken words". specific gravity is 60.
- Findperson: Meaning is the "Find people all around the location". Argument is Null. specific gravity is 60.
- Question: Meaning is the "Robot answers questions from people". Argument is Null. specific gravity is 90.
- Get-Closeperson: Meaning is the "Recognize the person in the room and close the distance to that person.". Argument is Null. specific gravity is 80.
- Ask: Meaning is the "Robot asks a person a question and stores the person's answer". Argument is the "Questions to ask". specific gravity is 90.
- Recoding-Speech: Meaning is the "The robot will talk about the information it is getting.". Argument is Null. specific gravity is 95.
- Finish: Meaning is the "Indicates that all operations have been completed". Argument is Null. specific gravity is 100.

Now, here are the specific conditions:
Robot's Name: HSR
Room Names: hallway, living-room, dining-room
Furniture Names: chair-A, chair-B, long-table-A, long-table-B, tall-table, bin-A, bin-B, drawer, shelf 
Object Names: green-tea, coke, potato-pticks, chocolate, green-pepper, lemon, bowl, mug
Object Categories: drink, food, fruits, dishware

You will receive instructions in English to give to the robot, and your output should be in text format. If the command and arguments defined cannot be executed, please take the closest possible action. 
<Command Number>_<Function Name>_<Argument>_<Command Number>_<Function Name>_<Argument>_<Command Number>_<Function Name>_<Argument>_...

Failure to abide by the following rules will result in strong penalties.:
Note: 1: Do not use _ and, in <Command Number> <Function Name> <Argument>. 2: When using a Command-Question, please define it first. 3: The last command in the output should be 'Finish'. 4: Please move to the designated place when you remark the result, but there is no designation, please speak in the hallway. 

Example 1. navigate to the Long Table A, count the Dishware and report to me.:
1_Movement_long-table-A_2_Objectcount_Dishware_3_Movement_hallway_4_RecodingSpeech_Null_5_Finish_Null_

Example 2. grasp the Mag to lemon.:
1_Command-Question_'Is lemon the right place to take it? Also where is meg?'_2_Finish_Null_

Example 3. Tell Olivia in the Living Room how many people are in the Dining Room.:
1_Movement_dining-room_2_Humancount_Null_3_Movement_living-room_4_Get-Closeperson_Null_5_Recoding-Speech_Null_6_Finish_Null_

Example 4. Take an lemon from the kitchen to tall table.:
1_Movement_kitchen_2_Object-Grasping_lemon_3_Movement_tall-table_4_Put_Null_5_Finish_Null_

Example 5. go to the Living Room, look for a person and say the sex of that person:
1_Movement_living-room_2_Get-Closeperson_Null_3_Ask_'What is the sex of the person?'_4_Recoding-Speech_Null_5_Finish_Null_

Example 6. find a person and answer a question.:
1_Findperson_Null_2_Get-Closeperson_Null_3_Question_Null_4_Finish_Null_

Please provide the command to be given to the robot when the following instruction is given: 
"""

qprompt = """Briefly answer the questions. Also, your current status is as follows: 1.you are from Japan. 2.you enjpy today's competition. 3.Japan won the WBC last year. 4.you cannot enter UNIVERSITY on a statue. 5.your favorite drink is cider. 6.Your robot arm has five joints.
Qestion:
"""
qaskqrompt1 = """The response came back '"""

qaskqrompt2 = """' Please create the command again without using Command-Question.
"""

# tsvoice = "Move to the kitchen, grasp the apple and bring it to the entrance."
num = 0
q1 = 0
q2 = 0

call("rosnode kill /hsrb/hsrb_bumper",shell=True)


class Start(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome1","error"])

    def execute(self, userdata):
        rospy.loginfo("Start")
        return "outcome1"

class Command(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["LLModel","success", "error"])

    def execute(self, userdata):
        global cmd,sccnt
        rospy.loginfo("Command")
        rospy.loginfo("命令を聞き取る")
        cmd = input("コマンド？> ")
        return "LLModel"
        
class LLModel(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2","error"])

    def execute(self, userdata):
        global cmd,flow,LLMinput
        rospy.loginfo("LLModel")
        LLMinput = LLMprompt + cmd
        rospy.loginfo(LLMinput)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": "You are a technician giving commands to a home-working robot."},
            {"role": "user", "content": LLMinput}
            ],
            temperature=0.1
        )
        flow = completion.choices[0].message.content
        rospy.loginfo(flow)
        return "outcome2"

class Change(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome3", "Speech-Synthesis", "Ask", "Getcloser", "ObjectGrasping", "Put", "Movement", "error", "RecodingSpeech", "Objectcount", "Humancount", "Findperson", "Question", "CommandQuestion"])
    def execute(self, userdata):
        global flow,change_cnt,num,request
        rospy.loginfo("Change")
        flag = False
        s = flow.split("_")
        for i in s:
            num += 1
            if s[num] == "Finish":
                return "outcome3"
            elif s[num] == "Movement":
                request = s[num + 1]
                return "Movement"
            elif s[num] == "Object-Grasping":
                request = s[num + 1]
                return  "ObjectGrasping"
            elif s[num] == "Speech-Synthesis":
                request = s[num + 1]
                return "Speech-Synthesis"
            elif s[num] == "Ask":
                request = s[num + 1]
                return "Ask"
            elif s[num] == "Put":
                request = s[num + 1]
                return "Put"
            elif s[num] == "Command-Question":
                request = s[num + 1]
                return "CommandQuestion"
            elif s[num] == "Question":
                return "Question"
            elif s[num] == "Humancount":
                return "Humancount"  
            elif s[num] == "Objectcount":
                return "Objectcount"
            elif s[num] == "Recoding-Speech":
                return "RecodingSpeech"
            elif s[num] == "Get-Closeperson":
                return "Getcloser"
            elif s[num] == "Findperson":
                return "Findperson"
            else:
                continue

class CommandQuestion(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('CommandQuestion')
        return "outcome2"
    
class Question(smach.State): #HSRが質問に答える
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])

    def execute(self, userdata):
        rospy.loginfo("Question")
        return "outcome2"
    
class Findperson(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])

    def execute(self, userdata):
        rospy.loginfo('Findperson')
        return "outcome2"

class Humancount(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])

    def execute(self, userdata):
        rospy.loginfo('Humancount')
        return "outcome2"
    
class Objectcount(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])

    def execute(self, userdata):
        rospy.loginfo('Objectcount')
        return "outcome2"

class SpeechSynthesis(smach.State): #LLMステートで作った発言を言う
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('SpeechSynthesis')
        return "outcome2"
    
class RecodingSpeech(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('RecodingSpeech')
        return "outcome2"

class Ask(smach.State): #LLMステートで作った質問を問いかける
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('Ask')
        return "outcome2"

class Getcloser(smach.State): #人に近づく
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('Getcloser')
        return "outcome2"

class ObjectGrasping(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('ObjectGrasping')
        return "outcome2"
    
class Put(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('Put')
        return "outcome2"

class Movement(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome2"])
    
    def execute(self, userdata):
        rospy.loginfo('Movement')
        return "outcome2"

class Service(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=["outcome1"])

    def execute(self, userdata):
        rospy.loginfo("go inspection")
        return "outcome1"

def main():

    rospy.init_node("sample")
    sm_main = smach.StateMachine(outcomes=['EXIT'])

    with sm_main:
        smach.StateMachine.add('START', Start(), transitions={'outcome1':'COMMAND',
                                                              'error':'START'})

        smach.StateMachine.add('COMMAND', Command(), transitions={'LLModel':'LLMODEL',
                                                                  'success':'EXIT',
                                                                  'error':'COMMAND'})

        smach.StateMachine.add('LLMODEL', LLModel(), transitions={'outcome2':'CHANGE',
                                                              'error':'LLMODEL'})

        smach.StateMachine.add('CHANGE', Change(), transitions={  'Speech-Synthesis':'SpeechSynthesis',
                                                                  'ObjectGrasping':'ObjectGrasping',
                                                                  'Movement':'Movement',
                                                                  'Put':'Put',
                                                                  'Ask':'Ask',
                                                                  'Getcloser':'Getcloser',
                                                                  'RecodingSpeech':'RecodingSpeech',
                                                                  'Objectcount':'Objectcount',
                                                                  'Humancount':'Humancount',
                                                                  'Findperson':'Findperson',
                                                                  'Question':'Question',
                                                                  'CommandQuestion':'CommandQuestion',
                                                                  'error':'CHANGE',
                                                                  'outcome3':'SERVICE'})

        smach.StateMachine.add('CommandQuestion', CommandQuestion(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Question', Question(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Findperson', Findperson(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Humancount', Humancount(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Objectcount', Objectcount(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('SpeechSynthesis', SpeechSynthesis(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('RecodingSpeech', RecodingSpeech(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Ask', Ask(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Getcloser', Getcloser(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('ObjectGrasping', ObjectGrasping(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Put', Put(), transitions={'outcome2':'CHANGE'})

        smach.StateMachine.add('Movement', Movement(), transitions={'outcome2':'CHANGE'})


        smach.StateMachine.add('SERVICE', Service(), transitions={'outcome1':'COMMAND'})
    sis = smach_ros.IntrospectionServer('smach_server', sm_main, '/SM_ROOT')
    sis.start()
    sm_main.execute()
    sis.stop()

if __name__ == '__main__':
    main()
