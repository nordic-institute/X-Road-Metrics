from pymongo import MongoClient
from pymongo import ASCENDING as ASC

indexRequests = [
    {
        'db': 'query_db',
        'collection': 'raw_messages',
        'indexes': [
            [('requestInTs', ASC)],
            [('corrected', ASC), ('requestInTs', ASC)]
        ]
    },

    {
        'db': 'query_db',
        'collection': 'clean_data',
        'indexes': [
            [('clientHash', ASC)],
            [('producerHash', ASC)],
            [('correctorTime', ASC)],
            [('correctorStatus', ASC), ('client.requestInTs', ASC)],
            [('correctorStatus', ASC), ('producer.requestInTs', ASC)],
            [('messageId', ASC), ('client.requestInTs', ASC)],
            [('messageId', ASC), ('producer.requestInTs', ASC)],
            [('client.requestInTs', ASC)],
            [('client.serviceCode', ASC)],
            [('producer.requestInTs', ASC)],
            [('producer.serviceCode', ASC)],
            [('client.clientMemberCode', ASC), ('client.clientSubsystemCode', ASC), ('client.requestInTs', ASC)],
            [('client.serviceMemberCode', ASC), ('client.serviceSubsystemCode', ASC), ('client.requestInTs', ASC)],
            [('producer.clientMemberCode', ASC), ('producer.clientSubsystemCode', ASC), ('producer.requestInTs', ASC)],
            [('producer.serviceMemberCode', ASC), ('producer.serviceSubsystemCode', ASC), ('producer.requestInTs', ASC)]
        ]
    },

    {
        'db': 'collector_state',
        'collection': 'server_list',
        'indexes': [[('timestamp', ASC)]]
    },

    {
        'db': 'reports_state',
        'collection': 'notification_queue',
        'indexes': [
            [('status', ASC), ('user_id', ASC)]
        ]
    },

    {
        'db': 'analyzer_database',
        'collection': 'incident',
        'indexes': [
            [('incident_status', ASC), ('incident_creation_timestamp', ASC)]
        ]
    },
]


def create_indexes(xroad_instance: str, client: MongoClient):
    count = 0
    for request in indexRequests:
        db = f"{request['db']}_{xroad_instance}"
        collection = request['collection']

        for index in request['indexes']:
            try:
                client[db][collection].create_index(index)
                count += 1
            except Exception as e:
                print(f"Failed to create index: {e}")

    print(f"Created {count} indexes.")
