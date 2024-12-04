
REM $env:ENV_NAME=$environment
set ENV_NAME=rd-perf01

set vUsers=25
set rampUp=1
set runTime="3m"



locust -f tests\TestCollection.py --host "http://localhost" --autostart -u %vUsers% -r %rampUp% --autostart 
