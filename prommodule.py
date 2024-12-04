import http.client
import logging
import os
import time

# from locust.runners import STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP, MasterRunner, LocalRunner, WorkerRunner
# import gevent
# from threading import Timer


path = "/tmp"


def on_stop(environment, **kwargs):
    if environment.web_ui:
        time.sleep(3)
        s = environment.stats

        push_gateway = os.environ.get('PROM_PUSHGATEWAY')
        if push_gateway is not None:
            send_stats_to_pushgateway(s)
        else:
            print('Not sending status to push gateway')

        if environment.stats.total.fail_ratio > 0.1:
            logging.error("Test failed due to failure ratio > 10%")
            environment.process_exit_code = 1
        else:
            environment.process_exit_code = 0


def _submit_wrapper(job_name, metric_name, metric_value):
    headers = {'X-Requested-With': 'Python requests', 'Content-type': 'text/xml'}
    data = '%s %s\n' % (metric_name, metric_value)
    conn = http.client.HTTPConnection(os.environ['PROM_PUSHGATEWAY'])
    conn.request("POST", "/metrics/job/%s" % (job_name), data, headers)
    conn.close


def send_stats_to_pushgateway(stats):
    s = stats.total
    arr = s.percentile()
    resp_per = arr.split()
    resp_per = resp_per[1:-1]
    num_requests = str(s.num_requests)
    num_failures = str(s.num_failures)
    ratio_failures = str(s.fail_ratio)
    target_per = resp_per[4]
    rps = s.total_rps

    jobname = os.environ['PROM_JOBNAME']

    entries = stats.entries
    list_entries = list(entries.keys())

    _submit_wrapper(jobname, 'locust_total_requests', num_requests)
    _submit_wrapper(jobname, 'locust_total_failures', num_failures)
    _submit_wrapper(jobname, 'locust_ratio_failures', ratio_failures)
    _submit_wrapper(jobname, 'locust_90th_percentile', target_per)
    _submit_wrapper(jobname, 'locust_requests_per_second', str(rps))

    for ent in list_entries:
        name = ent[0]
        method = ent[1]
        var_percentile = stats.get(name, method).get_response_time_percentile(0.90)
        var_requests = stats.get(name, method).num_requests
        var_failures = stats.get(name, method).num_failures
        var_failureratio = stats.get(name, method).fail_ratio
        var_rps = stats.get(name, method).total_rps

        _submit_wrapper(jobname, 'locust_' + name + '_requests', var_requests)
        _submit_wrapper(jobname, 'locust_' + name + '_failures', var_failures)
        _submit_wrapper(jobname, 'locust_' + name + '_failures_ratio', var_failureratio)
        _submit_wrapper(jobname, 'locust_' + name + '_90th_percentile', var_percentile)
        _submit_wrapper(jobname, 'locust_' + name + '_requests_per_second', str(var_rps))


'''
def error_rate_check(environment):
    while not environment.runner.state in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        time.sleep(1)
        if environment.runner.stats.total.fail_ratio > 0.5:
            print(f"fail ratio was {environment.runner.stats.total.fail_ratio}, quitting")
            environment.runner.quit()
            return

def time_check(environment):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(error_rate_check, environment)

'''
