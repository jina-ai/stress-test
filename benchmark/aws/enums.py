from enum import Enum


class SSMCreationStatus(Enum):
    SUCCESS = ['Active']
    WAIT = ['Creating', 'Updating', 'Pending']
    FAILURE = ['Failed']
    

class SSMCreationTime(Enum):
    TIMEOUT = 120
    SLEEP = 5
    

class SSMAssociationStatus(Enum):
    SUCCESS = ['Active']
    WAIT = ['Creating', 'Updating', 'Pending']
    FAILURE = ['Failed']
    
    
class SSMAssociationTime(Enum):
    TIMEOUT = 120
    SLEEP = 5
    
    
class SSMDeletionStatus(Enum):
    SUCCESS = ['Deleted']
    WAIT = ['Deleting', 'Pending']
    FAILURE = ['Failed']


class SSMDeletionTime(Enum):
    TIMEOUT = 120
    SLEEP = 5


class PluginStatus(Enum):
    SUCCESS = ['Success']
    WAIT = ['Pending', 'InProgress', 'Delayed']
    FAILURE = ['Cancelled', 'TimedOut', 'Failed', 'Cancelling']


class PluginTime(Enum):
    TIMEOUT = 14400
    SLEEP = 10
