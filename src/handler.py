import os

from src.config import CONFIG
from src.rds import RDS
from src.utils import enable_triggers, describe_db_clusters, start_db_cluster, disable_triggers, stop_db_cluster, \
    purge_queue
import logging

TEST_DB = 'nwcapture-test'
QA_DB = 'nwcapture-qa'
SQS_TEST = 'aqts-capture-trigger-queue-TEST'
SQS_QA = 'aqts-capture-trigger-queue-QA'

TEST_LAMBDA_TRIGGERS = ['aqts-capture-trigger-TEST-aqtsCaptureTrigger',
                        'aqts-capture-trigger-tmp-TEST-aqtsCaptureTrigger']
QA_LAMBDA_TRIGGERS = ['aqts-capture-trigger-QA-aqtsCaptureTrigger']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def start_test_db(event, context):
    started = start_db(TEST_DB, TEST_LAMBDA_TRIGGERS, SQS_TEST)
    return {
        'statusCode': 200,
        'message': f"Started the test db: {started}"
    }


def start_qa_db(event, context):
    started = start_db(QA_DB, QA_LAMBDA_TRIGGERS, SQS_QA)
    return {
        'statusCode': 200,
        'message': f"Started the qa db: {started}"
    }


def stop_test_db(event, context):
    stopped = stop_db(TEST_DB, TEST_LAMBDA_TRIGGERS)
    return {
        'statusCode': 200,
        'message': f"Stopped the test db: {stopped}"
    }


def stop_qa_db(event, context):
    stopped = stop_db(QA_DB, QA_LAMBDA_TRIGGERS)
    return {
        'statusCode': 200,
        'message': f"Stopped the qa db: {stopped}"
    }


def start_db(db, triggers, queue_name):
    purge_queue(queue_name)
    cluster_identifiers = describe_db_clusters("start")
    started = False
    for cluster_identifier in cluster_identifiers:
        if cluster_identifier == db:
            start_db_cluster(db)
            started = True
            enable_triggers(triggers)
    return started


def stop_db(db, triggers):
    cluster_identifiers = describe_db_clusters("stop")
    stopped = False
    disable_triggers(triggers)
    for cluster_identifier in cluster_identifiers:
        if cluster_identifier == db:
            stop_db_cluster(db)
            stopped = True
    return stopped


def stop_test_observations_db(event, context):
    logger.debug("enter stop_test_observations_db")
    # 1. query the
    sql = "select count(1) from batch_job_execution where status not in ('COMPLETED')"
    rds = RDS()

    logger.debug(f"about to run query {sql}")
    result = rds.execute_sql(sql)
    if result[0] > 0:
        logger.debug("something is running")
    elif result[0] == 0:
        logger.debug("nothing is running")
    else:
        raise Exception(f"something wrong with db result {result}")
    # boto3.client('rds').stop_db_instance(DBInstanceIdentifier='observation-test')

    logger.debug("exit stop_test_observations_db")
