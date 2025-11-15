11/04/2025 5PM
I need to simulate what a bank with threads with 3 tellers 50customers. tellers have to use charged resources such as manager safe and door. I will be using python for this threading 


11/10/2025 1pm
I added bank.py file to have the main code so far 
what we know is that there is  50 customers walking trough the door (2max) 3 tellers available that are shareing resources such as the manager (1max) safe (2max) 

impliemented some of the main teller and customer interactions
as well as the shared resources class
added the function where bank can open and keep track of costumers
added a line for clients 

Right now as I got the code to work i am having problems with the order in which the prints are going since im getting something like this Customer 14 [Door]: entered

Customer 19 [—]: waits in line
Teller 1 [Safe]: transaction done
Customer 40 [—]: arrival wait done
Teller 1 [Safe]: done with safe
Customer 40 [Door]: entering
Teller 1 [Customer 28]: completes transaction
where teller is not even doing the right oder of actions

11/11/2025 
Was able to fix the order in wich the outputs we coming out now the output is looking like this 
Teller 0 [—]: ready to serve
Teller 1 [—]: ready to serve
Teller 2 [—]: ready to serve
Teller 2 [—]: bank is now open
Customer 1 [—]: arrival wait 4ms start
Customer 2 [—]: arrival wait 3ms start
Customer 3 [—]: arrival wait 46ms start
Customer 4 [—]: arrival wait 59ms start
Customer 5 [—]: arrival wait 40ms start
Customer 6 [—]: arrival wait 48ms start
Customer 7 [—]: arrival wait 54ms start
Customer 8 [—]: arrival wait 67ms start
Customer 9 [—]: arrival wait 21ms start
Customer 10 [—]: arrival wait 71ms start
Customer 11 [—]: arrival wait 22ms start
Customer 12 [—]: arrival wait 30ms start
Customer 13 [—]: arrival wait 29ms start
Customer 2 [—]: arrival wait done
Customer 14 [—]: arrival wait 3ms start
Customer 2 [Door]: entering
Customer 15 [—]: arrival wait 22ms start
Customer 2 [Door]: entered
Customer 1 [—]: arrival wait done
Customer 2 [Teller 0]: selects teller
Customer 1 [Door]: entering
Customer 2 [Teller 0]: introduces self
Customer 1 [Door]: entered


11/15/25 1pm

added comments to the code as well as link to github into the read me 