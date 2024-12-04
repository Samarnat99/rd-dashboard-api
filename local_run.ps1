
#$env:ENV_NAME=$environment
$env:ENV_NAME="na-perf01-US"

# $vUsers = 10
# $rampUp = 10
# $runTime = "10m"

#cp ..\api-perf-testing\data\common\prommodule.py .\Module\prommodule.py
#cp .\common\readconfig.py .\Module\readconfig.py
#cp .\common\env_configs.json .\Module\env_configs.json
#cp .\common\data.csv .\Module\data.csv

#locust -f .\Module\test.py --host "http://localhost" -u $vUsers -r $rampUp --autostart --run-time $runTime



#locust -f .\tests\Wallet\test.py --host "http://localhost" -u $vUsers -r $rampUp --autostart --run-time $runTime

#locust -f .\Module\test.py,.\Paypal\test.py --host "http://localhost" -u $vUsers -r $rampUp --autostart --run-time $runTime

# locust -f .\tests\TestCollection.py --host "http://localhost" -u 5 -r 5 --autostart --run-time 30s
locust -f .\tests\TestCollection.py --host "http://localhost" --autostart

#locust -f .\tests\Wallet\test.py,.\tests\Paypal\test.py --host "http://localhost" -u $vUsers -r $rampUp --autostart --run-time $runTime