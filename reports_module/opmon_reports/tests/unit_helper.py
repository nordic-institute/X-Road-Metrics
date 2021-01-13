import collections
import hashlib
import random
import time
import uuid

from . import field_names

# Regular Match
# abs(Producer(requestInTs) - Client(requestInTs)) < 30_seconds
delta_30_seconds = 30 * 1000

# Orphan Match
# abs(Producer(requestInTs) - Client(requestInTs)) == any

# Assume all the same for XRoadInstance
# Pool format: (XRoadInstance, MemberClass, MemberCode, SubsystemCode)
machine_pool = list()
machine_pool.append(("CI-REPORTS", "MemberClass001", "MemberCode001", "SubsystemCode001"))
machine_pool.append(("CI-REPORTS", "MemberClass002", "MemberCode002", "SubsystemCode002"))
machine_pool.append(("CI-REPORTS", "MemberClass003", "MemberCode003", "SubsystemCode003"))
machine_pool.append(("CI-REPORTS", "MemberClass004", "MemberCode004", "SubsystemCode004"))
machine_pool.append(("CI-REPORTS", "MemberClass005", "MemberCode005", "SubsystemCode005"))


def create_raw_document_pair(orphan_match=False,
                             start_request_in_ts=0,
                             end_request_in_ts=100000,
                             document_succeeded=True,
                             specify_client_machine=None,
                             specify_producer_machine=None,
                             force_random_machine=False):

    # If specific values are set, change the machine identification
    if specify_client_machine is not None:
        client_machine = specify_client_machine
    else:
        client_machine = random.choice(machine_pool)

    if specify_producer_machine is not None:
        producer_machine = specify_producer_machine
    else:
        producer_machine = random.choice(machine_pool)

    # If needed, select service that are random (not inside the 5 options)
    if force_random_machine:
        client_machine = (str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()))
        producer_machine = (str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()))

    query_from_client = {}
    query_from_producer = {}

    # Message form client point of view
    for k in field_names.string_fields:
        query_from_client[k] = str(uuid.uuid4())
    for k in field_names.integer_fields:
        query_from_client[k] = random.randint(0, 100000)
    for k in field_names.boolean_fields:
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
    for k in field_names.string_fields:
        query_from_producer[k] = str(uuid.uuid4())
    for k in field_names.integer_fields:
        query_from_producer[k] = random.randint(0, 100000)
    for k in field_names.boolean_fields:
        query_from_producer[k] = random.choice([True, False])

    query_from_producer['succeeded'] = document_succeeded
    query_from_client['succeeded'] = document_succeeded

    # Consistent communication
    control_list = field_names.comparison_list_orphan if orphan_match else field_names.COMPARISON_LIST
    for k in control_list:
        query_from_producer[k] = query_from_client[k]

    # Mandatory fields
    query_from_producer['messageId'] = query_from_client['messageId']
    query_from_producer['securityServerType'] = 'Producer'
    query_from_client['securityServerType'] = 'Client'
    query_from_client['requestInTs'] = random.randint(start_request_in_ts, end_request_in_ts)
    query_from_producer['requestInTs'] = random.randint(start_request_in_ts, end_request_in_ts)

    if not orphan_match:
        # If regular pair, make sure that requestInTs is within 30 seconds
        delta_time = random.randint(0, delta_30_seconds)
        delta_end_time = query_from_client['requestInTs'] + delta_time
        if delta_end_time < end_request_in_ts:
            query_from_producer['requestInTs'] = delta_end_time
        else:
            query_from_producer['requestInTs'] = query_from_client['requestInTs']
    return query_from_client, query_from_producer


def create_clean_document(orphan_match=False,
                          request_attachment_count_is_zero=False,
                          response_attachment_count_is_zero=False,
                          corrector_status='processing',
                          matching_type='regular_pair',
                          start_request_in_ts=0,
                          end_request_in_ts=100000,
                          document_succeeded=True,
                          specify_client_machine=None,
                          specify_producer_machine=None,
                          force_random_machine=False):

    # Creates a valid pair of document
    client, producer = create_raw_document_pair(orphan_match, start_request_in_ts, end_request_in_ts,
                                                document_succeeded, specify_client_machine,
                                                specify_producer_machine, force_random_machine)

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
