def document_to_pair(document):
    """
    Extracts memberCode + subsystemCode + memberClass unique pairs from a given document.
    :param document: JSON document.
    :return: Returns a set with unique memberCode + subsystemCode + memberClass pairs from a given document.
    """
    cur_doc = document["_id"]
    pair_set = set()

    if "clientClientMemberCode" in cur_doc:
        if cur_doc["clientClientMemberCode"] is not None and cur_doc["clientClientSubsystemCode"] is not None:
            pair_set.add((cur_doc["clientClientMemberCode"], cur_doc["clientClientSubsystemCode"],
                          cur_doc["clientClientMemberClass"]))
        elif cur_doc["clientClientMemberCode"] is not None and cur_doc["clientClientSubsystemCode"] is None:
            pair_set.add((cur_doc["clientClientMemberCode"], "", cur_doc["clientClientMemberClass"]))

    if "clientServiceMemberCode" in cur_doc:
        if cur_doc["clientServiceMemberCode"] is not None and cur_doc["clientServiceSubsystemCode"] is not None:
            pair_set.add((cur_doc["clientServiceMemberCode"], cur_doc["clientServiceSubsystemCode"],
                          cur_doc["clientServiceMemberClass"]))
        elif cur_doc["clientServiceMemberCode"] is not None and cur_doc["clientServiceSubsystemCode"] is None:
            pair_set.add((cur_doc["clientServiceMemberCode"], "", cur_doc["clientServiceMemberClass"]))

    if "producerClientMemberCode" in cur_doc:
        if cur_doc["producerClientMemberCode"] is not None and cur_doc["producerClientSubsystemCode"] is not None:
            pair_set.add((cur_doc["producerClientMemberCode"], cur_doc["producerClientSubsystemCode"],
                          cur_doc["producerClientMemberClass"]))
        elif cur_doc["producerClientMemberCode"] is not None and cur_doc["producerClientSubsystemCode"] is None:
            pair_set.add((cur_doc["producerClientMemberCode"], "", cur_doc["producerClientMemberClass"]))

    if "producerServiceMemberCode" in cur_doc:
        if cur_doc["producerServiceMemberCode"] is not None and cur_doc["producerServiceSubsystemCode"] is not None:
            pair_set.add((cur_doc["producerServiceMemberCode"], cur_doc["producerServiceSubsystemCode"],
                          cur_doc["producerServiceMemberClass"]))
        elif cur_doc["producerServiceMemberCode"] is not None and cur_doc["producerServiceSubsystemCode"] is None:
            pair_set.add((cur_doc["producerServiceMemberCode"], "", cur_doc["producerServiceMemberClass"]))

    # Remove unnecessary results
    pair_set.discard(('producer.clientMemberCode', 'producer.clientSubsystemCode'))
    pair_set.discard(('producer.serviceMemberCode', 'producer.serviceSubsystemCode'))
    pair_set.discard(('client.clientMemberCode', 'client.clientSubsystemCode'))
    pair_set.discard(('client.serviceMemberCode', 'client.serviceSubsystemCode'))

    return pair_set


def documents_to_pairs(documents):
    """
    Go through all the given documents and append any new unique memberCode + subsystemCode + memberClass
    pair into the set.
    :param documents: List of JSON documents.
    :return: Returns a set of all the unique memberCode + subsystemCode + memberClass pairs from a list of documents.
    """
    pair_set = set()

    for document in documents:
        current_set = document_to_pair(document)
        pair_set = pair_set.union(current_set)

    return pair_set


def get_unique_pairs(db_manager):
    """
    Query the database and return all the unique memberCode + subsystemCode + memberClass pairs.
    :param db_manager: DatabaseManager object.
    :return: Returns all the unique memberCode + subsystemCode + memberClass pairs.
    """

    # Returns all the matching documents (both consumed & produced)
    list_of_documents = db_manager.get_all_unique_client_subsystems()

    pairs_set = documents_to_pairs(list_of_documents)

    return pairs_set
