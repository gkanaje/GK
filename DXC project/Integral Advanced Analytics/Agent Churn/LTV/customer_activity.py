import pyodbc
import pandas as pd
import os,sys,logging


defaulterSql='''select clnt.clntnum ,l.chdrnum,c.cnttype prd,case when effdate is null then 1 else 0 end defaultpayment ,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instto),112) instto,
CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112) instfrom,  l.instfreq,
case when l.instfreq='12' then case when effdate is null then 
  case when clnt.cltdob<=2
then 1 else 0 end else 0 end 
when l.instfreq='26' then case when effdate is null then 
case when datediff(MONTH,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112),getdate()) <=6 then 1
else 0 end else 0 end
when l.instfreq='01' then case when effdate is null then 
case when datediff(MONTH,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112),getdate()) <=12 then 1
else 0 end else 0 end
else null end recent_default,
datediff(MONTH,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112),getdate())
from vm1dta.linspf l
left outer join vm1dta.rtrnpf r on(rldgacct=chdrnum and rtrim(sacscode)='LP' 
and rtrim(sacstyp)='S' and effdate >= instfrom and effdate < INSTTO and validflag=1 and BATCTRCDE='B522'
and RLDGCOY=CHDRCOY and chdrcoy='2') 
inner join vm1dta.chdrpf c on(c.chdrnum = l.chdrnum and c.chdrcoy=l.CHDRCOY and c.validflag=1) 
inner join vm1dta.clntpf clnt on(clnt.clntnum = c.COWNNUM and clnt.CLNTCOY = c.COWNCOY)
where l.instfrom < cast(datepart(year,getdate())as varchar(4))+case when datepart(month,getdate())<10 then '0'+
cast(datepart(month,getdate()) as varchar(4)) else cast(datepart(month,getdate()) as varchar(4)) end+
case when datepart(day,getdate())<10 then '0'+
cast(datepart(day,getdate()) as varchar(4)) else cast(datepart(day,getdate()) as varchar(4)) end'''

engagementSql='''select t.*,PERCENT_RANK() OVER ( ORDER BY weighted_score)*100 percentile_rank
   from (select clntnum,
count(distinct prd) different_prd_cnt,count(distinct chdrnum) policycount,sum(defaultpayment) total_defaults,sum(recent_default) recentdefault_total ,
count(1) total_payments , (cast(sum(defaultpayment) as float)/cast(count(1) as float)) avg_defaults,
((count(distinct prd)*5)+(count(distinct chdrnum)*4)+(sum(approved_claims_count)*3)-((sum(cancelled_terminated_claims_count)*3)+(cast(sum(defaultpayment) as float)/cast(count(1) as float))*3)) weighted_score,
sum(approved_claims_count) total_approved_claims,
sum(cancelled_terminated_claims_count) total_cncl_terminated_claims,
case when datediff(DAY,max(purchase_date),getdate()) <= 1000 then 1 else 0 end recent_purchase,
datediff(YEAR,min(purchase_date),getdate()) yearsonfile,
cast(datediff(YEAR,min(purchase_date),getdate())/count(distinct chdrnum) as float) purchasefrequency from(
select clnt.clntnum ,l.chdrnum,c.cnttype prd,case when effdate is null then 1 else 0 end defaultpayment ,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instto),112) instto,
CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112) instfrom,  l.instfreq,
case when l.instfreq='12' then case when effdate is null then 
  case when datediff(MONTH,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112),getdate()) <=2
then 1 else 0 end else 0 end 
when l.instfreq='26' then case when effdate is null then 
case when datediff(MONTH,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112),getdate()) <=6 then 1
else 0 end else 0 end
when l.instfreq='01' then case when effdate is null then 
case when datediff(MONTH,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112),getdate()) <=12 then 1
else 0 end else 0 end
else null end recent_default,
datediff(MONTH,CONVERT(DATETIME,CONVERT(VARCHAR(8),l.instfrom),112),getdate()) delta,
CONVERT(DATETIME,CONVERT(VARCHAR(8),c.occdate),112) purchase_date,
case when claims.rgpystat ='AL' then 1 else 0 end approved_claims_count,
case when  claims.rgpystat in('BT','CL') then 1 else 0 end cancelled_terminated_claims_count
from vm1dta.linspf l
left outer join vm1dta.rtrnpf r on(rldgacct=chdrnum and rtrim(sacscode)='LP' 
and rtrim(sacstyp)='S' and effdate >= instfrom and effdate < INSTTO and validflag=1 and BATCTRCDE='B522'
and RLDGCOY=CHDRCOY and chdrcoy='2') 
inner join vm1dta.chdrpf c on(c.chdrnum = l.chdrnum and c.chdrcoy=l.CHDRCOY and c.validflag=1) 
inner join vm1dta.clntpf clnt on(clnt.clntnum = c.COWNNUM and clnt.CLNTCOY = c.COWNCOY)
left outer join vm1dta.regppf claims on(c.chdrnum = claims.chdrnum and c.chdrcoy=claims.CHDRCOY and claims.validflag=1) 
where l.instfrom < cast(datepart(year,getdate())as varchar(4))+case when datepart(month,getdate())<10 then '0'+
cast(datepart(month,getdate()) as varchar(4)) else cast(datepart(month,getdate()) as varchar(4)) end+
case when datepart(day,getdate())<10 then '0'+
cast(datepart(day,getdate()) as varchar(4)) else cast(datepart(day,getdate()) as varchar(4)) end )t
group by CLNTNUM)t'''

try:
	with pyodbc.connect('DSN=life_target2;UID=sisensedb_user;pwd=Sisense12#$') as conn:

		defaulterData=pd.read_sql(defaulterSql,conn)

		print(defaulterData.shape)

		defaulterData.to_csv('EX_SOURCE_PAYMENT_DEFAULTS_LIFE.csv',index=False)

		engagementData=pd.read_sql(engagementSql,conn)

		print(engagementData.shape)

		engagementData.to_csv('EX_SOURCE_ENGAGEMENT_SCORE_LIFE.csv',index=False)

		#possible implementation 
		'''with open ('default_query.sql') as sql:

			data=pd.read_sql_query(sql.read(),conn)

			data.to_csv('EX_SOURCE_PAYMENT_DEFAULTS_LIFE.csv',index=False)'''

except:
	print(sys.exc_info()[0])


