#!/bin/sh 

helm repo add influxdata https://helm.influxdata.com/

helm install -n influxdb influxdb influxdata/influxdb2 \
	--set service.type=LoadBalancer \
	--set service.loadBalancerIP=192.168.0.15 \
	--set adminUser.username=admin \
	--set adminUser.password=adminpassword \
	--set adminUser.token="78mdMPrH02UaKsrsb6Q2Ofj0neRVfRNDaFfrN2RWqreobbh3RtP7jyKX9-Ktvt-JBAthd1FPnZggkRANHi9T8w==" \
	--set adminUser.bucket=test
