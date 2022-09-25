# s3-storagebox-backup
Repo that hosts an action to backup an S3 server to a Hetzner StorageBox

Using the github action, a backup of minio.ci4rail.com is made periodically.
All files from all buckets are copied to the Hetzner StorageBox tied to `devserver1.ci4rail.com`.
It is always a full backup, older files on StorageBox are overwritten. New files from minio are added to StorageBox.

Currently the action runs on self-hosted runner on devserver2.ci4rail.com to have faster access to the data. 
