import json

from sentence_transformers import SentenceTransformer
import pandas as pd
from typing import List
import mysql.connector

STRING_UNKNOWN = "Sorry. I do not get it"

def get_list_questions():
    df = pd.read_csv("questions.txt", sep='\t')
    return df["question"].tolist()


def main():
    model = SentenceTransformer('roberta-large-nli-stsb-mean-tokens')

    sentences = get_list_questions()

    model.encode(sentences)

    from sklearn.cluster import KMeans

    num_clusters = 10
    clustering_model = KMeans(n_clusters=num_clusters)
    clustering_model.fit(model)
    cluster_assignment = clustering_model.labels_


class Answer:
    def __init__(self, answer: str, course_id: int):
        self.answer = answer
        self.course_id = course_id


class Intent:
    def __init__(self, id: int = 0, questions: List[str] = [],
        answers: List[Answer] = []):
        self.id = id
        self.question = questions
        self.answers = answers

    def get_intent_name(self):
        return "gmoodle_gen_intent_{}".format(self.id)

    def get_action_name(self):
        return "action_gmoodle_gen_{}".format(self.id)

    def get_action_class_naame(self):
        return "ActionGmoodleGen{}".format(self.id)

    def get_questions(self):
        return self.question

    def get_answer(self) -> List[Answer]:
        return self.answers


def generate_nlp(intents: List[Intent], file_name):
    with open(file_name, "w") as f:
        for intent in intents:
            f.write("## intent:{}\n".format(intent.get_intent_name()))
            for q in intent.get_questions():
                f.write("- {}\n".format(q))
            f.write("\n")


def generate_story(intents: List[Intent], file_name):
    with open(file_name, "w") as f:
        f.write("# gmoodle_gen_story.md\n\n"
                "## gmoodle_gen_path\n")
        for intent in intents:
            f.write("* {}\n"
                    "  - {}\n\n".format(intent.get_intent_name(),
                                    intent.get_action_name()))


def generate_python_code_for_intent(intent: Intent) -> str:
    ret = "class {}(Action):\n" \
          "    def name(self) -> Text:\n" \
          "        return \"{}\"\n" \
          "    def run(self, dispatcher: CollectingDispatcher,\n" \
          "        tracker: Tracker,\n" \
          "        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:\n" \
          "        course_id = get_course_id(tracker)\n".format(intent.get_action_class_naame(),
                                               intent.get_action_name())
    for ans in intent.get_answer():
        ret += "        if course_id == {}:\n" \
               "            dispatcher.utter_message(text=\"{}\")\n" \
               "            return []\n".format(ans.course_id, ans.answer)
    ret += "        dispatcher.utter_message(text=\"{}\")\n".format(STRING_UNKNOWN)
    ret += "        return []\n"
    return ret


def generate_intent_action(intents: List[Intent], file_name:str, base_action_py:str):
    with open(base_action_py, "r") as f_base_py:
        with open(file_name, "w") as f:
            f.writelines(f_base_py.readlines())
            f.write('\n')
            for intent in intents:
                f.write(generate_python_code_for_intent(intent))


def gen_intent_by_json(json: dict, id: int) -> Intent:
    answer = Answer(
        json["qa"]["a"],
        json["course_id"]
    )
    ret = Intent(
        id,
        json["qa"]["q"],
        [answer]
    )

    return ret


def gen_intents_by_json(data:List[dict]) -> List[Intent]:
    ret = []
    counter = 0
    for tuple in data:
        ret.append(gen_intent_by_json(tuple, counter))
        counter = counter + 1
    return ret

def get_data_json_from_simple_table(file_name):
    df = pd.read_csv(file_name, sep='\t')
    ret = []
    for index, row in df.iterrows():
        ret.append({
            "course_id": 27,
            "qa":{
                "q":[row["question"]],
                "a":row["answer"]
            }
        })
    return ret

def get_data_json_from_database(db_host, db_user, db_password, db_name):
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_password,
        database=db_name)
    df = pd.read_sql("SELECT * FROM mdl_eduhk_chatbot_qa", conn)

    ret = []
    counter = 0
    for index, row in df.iterrows():
        json_qa = json.loads(row["json_qa"])
        course_id = row["course_id"]

        for qa in json_qa:
            answers = []
            for a in qa["a"]:
                answers.append(Answer(a, course_id))

            ret.append(Intent(
                counter,
                qa["q"],
                answers
            ))

            counter += 1
    return ret

def main_gen():
    #todo: strcuture is not so good..
    # data = [{
    #     "qa": {"q": ["What is the weighting of assessments?"],
    #            "a": [{"course_id":8, ans:"Individual project (50%), Post reflection (10%),  Group project (30%), Class participation (10%)"}]
#            }}]
    #todo: remove generated nlp story
    #todo: grouping indent foreach each course ????
    intents = get_data_json_from_database(
        "gmoodle",
        "root",
        "gmoodle_123",
        "moodle"
    )

    generate_nlp(intents, "nlp")
    generate_story(intents, "story")
    generate_intent_action(intents, "my_action.py", "../actions.py")


if __name__ == "__main__":
    main_gen()
