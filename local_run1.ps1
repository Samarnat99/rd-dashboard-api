
#$env:ENV_NAME=$environment
$env:ENV_NAME="rd-perf01"

$vUsers = 1
$rampUp = 1
$runTime = "30m"



# locust -f .\tests\TestCollection.py --host "http://localhost" -u 5 -r 5 --autostart --run-time 30s test

# locust -f .\tests\ROA_WOO_Release_Spot_Mixed\roawoomix.py --host "http://localhost" --autostart -u $vUsers -r $rampUp --autostart --run-time $runTime

 locust -f "tests\categoryfuture\categoryfuture_1.py" --host "http://localhost" --autostart -u $vUsers -r $rampUp --autostart --run-time $runTime