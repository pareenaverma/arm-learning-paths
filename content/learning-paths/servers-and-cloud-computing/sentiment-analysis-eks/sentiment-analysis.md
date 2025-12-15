---
title: Set up Sentiment Analysis with Amazon EKS
weight: 4

### FIXED, DO NOT MODIFY
layout: learningpathall
---

## Installing the tools

You will need an [AWS account](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-creating.html). Create an account if needed. 

You also require multiple tools on your local computer. Follow these links to install each tool:

* [Kubectl](/install-guides/kubectl/).
* [AWS CLI](/install-guides/aws-cli/).
* [Docker](/install-guides/docker/).
* [Terraform](/install-guides/terraform/).
* [Java](/install-guides/java/).

To use the AWS CLI, you need to generate AWS access keys and configure the CLI. 

Follow the [AWS Credentials Install Guide](/install-guides/aws_access_keys/) for instructions on how to do this. 

## Set up Sentiment Analysis

Take a look at the [GitHub repository](https://github.com/koleini/spark-sentiment-analysis) then clone it on your local computer:

```console
git clone https://github.com/koleini/spark-sentiment-analysis.git
cd spark-sentiment-analysis/eks
```

If you would like to change the default AWS region, you can do this by editing the file `variables.tf`.

As you will see, the default value is at the top of the file and is set to `us-east-1`:

```output
variable "AWS_region" {
  default     = "us-east-1"
  description = "AWS region"
}
```

In addition, if you are using a profile other than `default`, then you need to update the following variable:

```output
variable "AWS_profile" {
  default     = "Your_AWS_Profile"
  description = "AWS authorization profile"
}
```

To create the Amazon EKS cluster, execute the following commands:

```bash
terraform init
terraform apply --auto-approve
```

Once the cluster is created, verify it in the AWS console.

{{% notice Note %}}
If you want to use an AWS CLI profile that is not the default, make sure that you change the profile name before running the command to verify the cluster.
{{% /notice %}} 

Update the `kubeconfig` file to access the deployed EKS cluster with the following command:

```bash
aws eks --region $(terraform output -raw region) update-kubeconfig --name $(terraform output -raw cluster_name) --profile <Your_AWS_Profile>
```

Create a service account for Apache Spark:

```bash
kubectl create serviceaccount spark
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=default:spark --namespace=default
```

## Build the sentiment analysis JAR file

Navigate to the `sentiment_analysis` folder to create a JAR file for the sentiment analyzer.

{{% notice Note %}}
JAR is an acronym for Java ARchive, and is a compressed archive file format that contains Java-related files and metadata.
{{% /notice %}}

You will need `sbt` installed. If you are running Ubuntu, you can install it with:

```bash
echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | sudo tee /etc/apt/sources.list.d/sbt.list
curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo gpg --dearmor -o /usr/share/keyrings/sbt-archive-keyring.gpg
sudo apt-get update
sudo apt-get install sbt
```

If you have another operating system, refer to [Installing sbt](https://www.scala-sbt.org/download.html).

```bash
cd ../sentiment_analysis
sbt assembly
```

A JAR file is created at the following location:

```output
sentiment_analysis/target/scala-2.13/bigdata-assembly-0.1.jar
```

## Create a Spark container image

Create a repository in Amazon ECR to store the docker images. You can also use Docker Hub.

The Spark repository contains a script to build the container image that you need to run inside the Kubernetes cluster. 

Execute this script on your Arm-based computer to build the arm64 image.

In the current working directory, use the following commands to get the Apache Spark tar file. 

Extract this file before building the image:

```bash
wget https://archive.apache.org/dist/spark/spark-3.5.3/spark-3.5.3-bin-hadoop3-scala2.13.tgz
tar -xvzf spark-3.5.3-bin-hadoop3-scala2.13.tgz
cd spark-3.5.3-bin-hadoop3-scala2.13
```

Copy the JAR file generated in the previous step to the following location:

```bash
cp ../sentiment_analysis/target/scala-2.13/bigdata-assembly-0.1.jar jars/
```

To build the Docker container, use the following commands, ensuring that you substitute the name of your container repository before executing them:

```bash
bin/docker-image-tool.sh -r <your-docker-repository> -t sentiment-analysis build
bin/docker-image-tool.sh -r <your-docker-repository> -t sentiment-analysis push
```

## Run Spark computation on the cluster

Execute the `spark-submit` command within the Spark folder to deploy the application. 

The following commands run the application with two executors, each with 12 cores. They allocate 24GB of memory for both the executors and driver pods.

 Before executing the `spark-submit` command, set the following variables (replacing values in angle brackets with your values):

```bash
export K8S_API_SERVER_ADDRESS=<K8S_API_SERVER_ENDPOINT>
export ES_ADDRESS=<IP_ADDRESS_OF_ELASTICS_SEARCH>
export CHECKPOINT_BUCKET=<S3_BUCKET_NAME>
export ECR_ADDRESS=<ECR_REGISTERY_ADDRESS>
```

Execute the `spark-submit` command:

```bash
bin/spark-submit \
      --class bigdata.SentimentAnalysis \
      --master k8s://K8S_API_SERVER_ADDRESS:443 \
      --deploy-mode cluster \
      --conf spark.executor.instances=2 \
      --conf spark.kubernetes.container.image=$ECR_ADDRESS \
      --conf spark.kubernetes.driver.pod.name="spark-twitter" \
      --conf spark.kubernetes.namespace=default \
      --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
      --conf spark.driver.extraJavaOptions="-DES_NODES=$ES_ADDRESS -DCHECKPOINT_LOCATION=s3a://$CHECKPOINT_BUCKET/checkpoints/" \
      --conf spark.executor.extraJavaOptions="-DES_NODES=$ES_ADDRESS -DCHECKPOINT_LOCATION=s3a://$CHECKPOINT_BUCKET/checkpoints/" \
      --conf spark.executor.cores=12 \
      --conf spark.driver.cores=12 \
      --conf spark.driver.memory=24g \
      --conf spark.executor.memory=24g \
      --conf spark.memory.fraction=0.8 \
      --name sparkTwitter \
      local:///opt/spark/jars/bigdata-assembly-0.1.jar
```

Use `kubectl get pods` to check the status of the pods in the cluster:

```output
NAME                                        READY   STATUS    RESTARTS   AGE
sentimentanalysis-346f22932b484903-exec-1   1/1     Running   0          10m
sentimentanalysis-346f22932b484903-exec-2   1/1     Running   0          10m
spark-twitter                               1/1     Running   0          12m
```

## X Sentiment Analysis

Create an X [developer account](https://developer.x.com/en/portal/dashboard) and download the bearer token. 

Use the following commands to set the bearer token and fetch the posts:

```bash
export BEARER_TOKEN=<BEARER_TOKEN_FROM_X>
python3 scripts/xapi_tweets.py
```

{{% notice Note %}}
You might need to install the following Python packages if you run into any dependency issues:

```bash
pip3 install requests
pip3 install boto3
```
{{% /notice %}}

You can modify the script `xapi_tweets.py` and use your own keywords. 

Here is the code which includes some sample keywords: 

```python
query_params = {'query': "(#onArm OR @Arm OR #Arm OR #GenAI) -is:retweet lang:en",
                'tweet.fields': 'lang'}
```

Use the following command to send these processed posts to Elasticsearch:

```bash
python3 csv_to_kinesis.py
```

Navigate to the Kibana dashboard using the following URL and analyze the posts:

```console
http://<IP_Address_of_ES_and_Kibana>:5601
```

## Environment clean-up

Following this Learning Path will deploy many artifacts in your cloud account. Remember to destroy the resources after you have finished. Use the following command to clean up the resources:

```bash
terraform destroy
```
