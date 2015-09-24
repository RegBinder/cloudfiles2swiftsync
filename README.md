# cloudfiles2swiftsync

This utility can be used to move all data from Rackspace Cloud Files to a private Swift cluster. Inspired from SwiftSync. It does not sync account metadata


to install

pip install -r requirements.txt

the automatically dependencies installer does not work yet.

Thanks so much to the team enovance for the work on SwiftSync. Originally we wanted to fork the work and add in the pyrax api to make SwiftSync work with CloudFiles. However we did not have time so we trimmed out what we did not need and added the pyrax api.