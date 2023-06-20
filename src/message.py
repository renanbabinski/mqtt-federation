import paho.mqtt.client as mqtt
import fnmatch
import logging
import pickle
from typing import Tuple
from enum import Enum
from topics import CORE_ANN_TOPIC_LEVEL, MEMB_ANN_TOPIC_LEVEL, FEDERATED_TOPICS_LEVEL, ROUTING_TOPICS_LEVEL, SUB_LOGS_TOPIC_LEVEL
from topics import CORE_ANNS, MEMB_ANNS, ROUTING_TOPICS, SUB_LOGS, FEDERATED_TOPICS


logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SubLog:
    def __init__(self, payload) -> None:
        self.payload = payload

class FederatedPub:
    def __init__(self, payload) -> None:
        self.payload = payload

class CoreAnn:
    def __init__(self, core_id, dist, sender_id) -> None:
        self.core_id = core_id
        self.dist = dist
        self.sender_id = sender_id

    def __str__(self) -> str:
        return f"CoreAnn(core_id={self.core_id}, dist={self.dist}, sender_id={self.sender_id})"

    def serialize(self, fed_topic: str) -> Tuple[str, bytes]:
        topic = f"{CORE_ANN_TOPIC_LEVEL}{fed_topic}"
        payload = pickle.dumps(self)

        return topic, payload

class Message(Enum):
    SubLog = SubLog
    FederatedPub = FederatedPub
    CoreAnn = CoreAnn


def deserialize(mqtt_msg: mqtt.MQTTMessage) -> Tuple[str, Message]:
    topic:str = mqtt_msg.topic

    # if topic.startswith(ROUTING_TOPICS_LEVEL):
    #     fed_topic = topic[len(ROUTING_TOPICS_LEVEL):]
    #     assert fed_topic, "Empty federated topic"
    #     routed_pub = mqtt_msg.payload.decode('utf-8')
    #     return fed_topic, Message("RoutedPub", routed_pub)

    # elif topic.startswith(MEMB_ANN_TOPIC_LEVEL):
    #     fed_topic = topic[len(MEMB_ANN_TOPIC_LEVEL):]
    #     assert fed_topic, "Empty federated topic"
    #     memb_ann = mqtt_msg.payload.decode('utf-8')
    #     return fed_topic, Message("MeshMembAnn", memb_ann)
    
    if topic.startswith(SUB_LOGS_TOPIC_LEVEL):
        fed_topic = mqtt_msg.payload.decode('utf-8').split(' ')[-1] ## Get last element (topic)
        # print(mqtt_msg.payload.decode('utf-8'))
        if  fnmatch.fnmatch(fed_topic, SUB_LOGS) or \
            fnmatch.fnmatch(fed_topic, ROUTING_TOPICS) or \
            fnmatch.fnmatch(fed_topic, MEMB_ANNS) or \
            fnmatch.fnmatch(fed_topic, FEDERATED_TOPICS) or \
            fnmatch.fnmatch(fed_topic, CORE_ANNS):
            
            logger.debug("SubLog Received in management topic - Droping Message...")
            return None, None
        else:
            payload = mqtt_msg.payload.decode('utf-8')
            sub_log = SubLog(
                payload=payload
            )
            return fed_topic, Message.SubLog.value(sub_log)
        
    elif topic.startswith(CORE_ANN_TOPIC_LEVEL):
        fed_topic = topic[len(CORE_ANN_TOPIC_LEVEL):]
        assert fed_topic, "Empty federated topic"
        core_ann = pickle.loads(mqtt_msg.payload)
        return fed_topic, core_ann
    
    # Federated Publications will ever be last match "#"
    elif topic.startswith(FEDERATED_TOPICS_LEVEL):
        fed_topic = topic[len(FEDERATED_TOPICS_LEVEL):]
        assert fed_topic, "Empty federated topic"
        # federated_pub = FederatedPub(mqtt_msg.payload)
        payload = mqtt_msg.payload.decode('utf-8')
        federated_pub = FederatedPub(
            payload=payload
        )
        return fed_topic, Message.FederatedPub.value(federated_pub)


    else:
        raise ValueError(f"Received a packet from a topic it was not supposed to be subscribed to {topic}")