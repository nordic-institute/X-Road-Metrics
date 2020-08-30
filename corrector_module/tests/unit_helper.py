import collections
import hashlib
import random
import time
import uuid

from corrector_module.tests.unit_settings import Settings

# From RIA
string_fields = [
    'securityServerInternalIp',
    'securityServerType',
    'clientXRoadInstance',
    'clientMemberClass',
    'clientMemberCode',
    'clientSubsystemCode',
    'serviceXRoadInstance',
    'serviceMemberClass',
    'serviceMemberCode',
    'serviceSubsystemCode',
    'serviceCode',
    'serviceVersion',
    'representedPartyClass',
    'representedPartyCode',
    'messageId',
    'messageUserId',
    'messageIssue',
    'messageProtocolVersion',
    'clientSecurityServerAddress',
    'serviceSecurityServerAddress',
    'soapFaultCode',
    'soapFaultString'
]

# Minimum value 0
integer_fields = [
    'monitoringDataTs',
    'requestInTs',
    'requestOutTs',
    'responseInTs',
    'responseOutTs',
    'requestSoapSize',
    'requestMimeSize',
    'requestAttachmentCount',
    'responseSoapSize',
    'responseMimeSize',
    'responseAttachmentCount'
]

boolean_fields = ['succeeded']

# Regular Match
# abs(Producer(requestInTs) - Client(requestInTs)) < 1_minute
delta_1_minute = 1 * 60 * 1000

# Orphan Match
# abs(Producer(requestInTs) - Client(requestInTs)) == any

# Assume all the same for XRoadInstance
# Pool format: (XRoadInstance, MemberClass, MemberCode, SubsystemCode)
machine_pool = list()
machine_pool.append(("CI-CORRECTOR", "MemberClass001", "MemberCode001", "SubsystemCode001"))
machine_pool.append(("CI-CORRECTOR", "MemberClass002", "MemberCode002", "SubsystemCode002"))
machine_pool.append(("CI-CORRECTOR", "MemberClass003", "MemberCode003", "SubsystemCode003"))
machine_pool.append(("CI-CORRECTOR", "MemberClass004", "MemberCode004", "SubsystemCode004"))
machine_pool.append(("CI-CORRECTOR", "MemberClass005", "MemberCode005", "SubsystemCode005"))


def create_raw_document_pair(orphan_match=False):
    settigs = Settings()

    # Sample machines from machine pool
    client_machine = random.choice(machine_pool)
    producer_machine = random.choice(machine_pool)

    query_from_client = {}
    query_from_producer = {}

    # Message form client point of view
    for k in string_fields:
        query_from_client[k] = str(uuid.uuid4())
    for k in integer_fields:
        query_from_client[k] = random.randint(0, 100000)
    for k in boolean_fields:
        query_from_client[k] = random.choice([True, False])

    # Add sample machine information
    query_from_client['clientXRoadInstance'] = client_machine[0]
    query_from_client['clientMemberClass'] = client_machine[1]
    query_from_client['clientMemberCode'] = client_machine[2]
    query_from_client['clientSubsystemCode'] = client_machine[3]
    query_from_client['serviceXRoadInstance'] = producer_machine[0]
    query_from_client['serviceMemberClass'] = producer_machine[1]
    query_from_client['serviceMemberCode'] = producer_machine[2]
    query_from_client['serviceSubsystemCode'] = producer_machine[3]

    # Message form producer point of view
    for k in string_fields:
        query_from_producer[k] = str(uuid.uuid4())
    for k in integer_fields:
        query_from_producer[k] = random.randint(0, 100000)
    for k in boolean_fields:
        query_from_producer[k] = random.choice([True, False])

    # Consistent communication
    control_list = settigs.comparison_list_orphan if orphan_match else settigs.COMPARISON_LIST
    for k in control_list:
        query_from_producer[k] = query_from_client[k]

    # Mandatory fields
    query_from_producer['messageId'] = query_from_client['messageId']
    query_from_producer['securityServerType'] = 'Producer'
    query_from_client['securityServerType'] = 'Client'

    # Force requestInTs to be valid
    delta_time = random.randint(0, delta_1_minute)
    query_from_producer['requestInTs'] = query_from_client['requestInTs'] + delta_time

    return query_from_client, query_from_producer


def calculate_hash(_document):
    """
    Hash the given document with MD5 and remove _id & insertTime parameters.
    :param _document: The input documents.
    :return: Returns the monitoringDataTs_document_hash string.
    """
    document = _document.copy()
    doc_hash = None
    if document is not None:
        od = collections.OrderedDict(sorted(document.items()))
        od.pop('_id', None)
        od.pop('insertTime', None)
        od.pop('corrected', None)
        json_str = str(od)
        doc_hash = hashlib.md5(json_str.encode('utf-8')).hexdigest()
    return "{0}_{1}".format(document['monitoringDataTs'], doc_hash)


def create_clean_document(orphan_match=False,
                          request_attachment_count_is_zero=False,
                          response_attachment_count_is_zero=False,
                          corrector_status='processing',
                          matching_type='regular_pair'):
    # Creates a valid pair of document
    client, producer = create_raw_document_pair(orphan_match)

    # Control condition to build tests
    if request_attachment_count_is_zero:
        client['requestAttachmentCount'] = 0
        producer['requestAttachmentCount'] = 0
    else:
        client['requestAttachmentCount'] += 1
        producer['requestAttachmentCount'] += 1

    if response_attachment_count_is_zero:
        client['responseAttachmentCount'] = 0
        producer['responseAttachmentCount'] = 0
    else:
        client['responseAttachmentCount'] += 1
        producer['responseAttachmentCount'] += 1

    clean_doc = dict()
    clean_doc['messageId'] = client['messageId']
    clean_doc['client'] = client
    clean_doc['clientHash'] = calculate_hash(client)
    clean_doc['producer'] = producer
    clean_doc['producerHash'] = calculate_hash(producer)

    clean_doc['clientSsRequestDuration'] = client['requestOutTs'] - client['requestInTs']
    clean_doc['clientSsResponseDuration'] = client['responseOutTs'] - client['responseInTs']
    clean_doc['clientRequestSize'] = client['requestMimeSize'] if client['requestAttachmentCount'] > 0 else client[
        'requestSoapSize']
    clean_doc['clientResponseSize'] = client['responseMimeSize'] if client['responseAttachmentCount'] > 0 else client[
        'responseSoapSize']

    clean_doc['producerDurationClientView'] = client['responseInTs'] - client['requestOutTs']
    clean_doc['producerDurationProducerView'] = producer['responseOutTs'] - producer['requestInTs']
    clean_doc['producerSsRequestDuration'] = producer['requestOutTs'] - producer['requestInTs']
    clean_doc['producerSsResponseDuration'] = producer['responseOutTs'] - producer['responseInTs']
    clean_doc['producerIsDuration'] = producer['responseInTs'] - producer['requestOutTs']
    clean_doc['producerRequestSize'] = producer['requestMimeSize'] if producer['requestAttachmentCount'] > 0 else \
        producer['requestSoapSize']
    clean_doc['producerResponseSize'] = producer['responseMimeSize'] if producer['responseAttachmentCount'] > 0 else \
        producer['responseSoapSize']

    clean_doc['totalDuration'] = client['responseOutTs'] - client['requestInTs']
    clean_doc['requestNwDuration'] = producer['requestInTs'] - client['requestOutTs']
    clean_doc['responseNwDuration'] = client['responseInTs'] - producer['responseOutTs']
    clean_doc['correctorTime'] = float(time.time())
    clean_doc['correctorStatus'] = corrector_status
    clean_doc['matchingType'] = matching_type
    return clean_doc
