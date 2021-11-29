#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib import pyplot as plt
from sklearn.preprocessing import LabelEncoder,StandardScaler
from lifelines.utils import to_long_format
import matplotlib.pyplot as plt
import sys
from lifelines import CoxPHFitter
from lifelines.utils import k_fold_cross_validation


# In[2]:


#eventually the db data based on query
'''select distinct clntnum,
c.cltsex,
rtrim(c.GIVNAME)+' '+rtrim(c.SURNAME) client_name,
c.marryd,
occpcode,
upper(c.CLTADDR05) clientregion,
case when (select count(1) from 
vm1dta.ustfpf u,vm1dta.chdrpf pol 
where pol.CHDRNUM=u.chdrnum and pol.COWNNUM=c.clntnum and pol.VALIDFLAG=1) >0 
then 1 else 0 end marketbased, --market product identified based on transactions in ustfpf
case when entry_age between 0 and 20 then 'young age'
when entry_age between 21 and 50 then 'working age group' 
when entry_age between 51 and 60 then 'old age' 
when entry_age > 60 then 'retired group'
end entry_age, --entry age used instead of current age
case when (select count(1) from vm1dta.chdrpf pol 
where pol.VALIDFLAG=1 and pol.STATCODE ='IF' and pol.COWNNUM = c.clntnum and pol.CURRTO=99999999) > 0 then 0 else 1 end 
churn,
case when amtpaid >= 0 and amtpaid <= 100000 then 'low value' 
when amtpaid >= 100001 and amtpaid <= 1000000 then 'medium value' 
when  amtpaid > 1000001 then 'high value' 
end amtpaid,
case when (select datediff(day,cast(cast(min(occdate) as varchar(8)) as date),getdate()) from vm1dta.chdrpf pol where pol.COWNNUM = c.CLNTNUM and pol.VALIDFLAG=1) <0 then 10 
else  (select datediff(day,cast(cast(min(occdate) as varchar(8)) as date),getdate()) from vm1dta.chdrpf pol where pol.COWNNUM = c.CLNTNUM and pol.VALIDFLAG=1) end elapseddays
from vm1dta.clntpf c,
(select min(ANBCCD) entry_age,COWNNUM
from vm1dta.lifepf l,vm1dta.chdrpf pol  where l.chdrnum=pol.chdrnum and life='01' and l.VALIDFLAG=1 and pol.VALIDFLAG
=1 and l.lifcnum=pol.COWNNUM group by COWNNUM) age_band,
(select c.cownnum,sum(acctamt) amtpaid from vm1dta.rtrnpf r,vm1dta.chdrpf c 
where r.rldgacct=c.chdrnum and rtrim(r.sacscode)='LP' and rtrim(r.sacstyp)='S' and c.validflag=1 and r.BATCTRCDE='B522'
group by c.cownnum) total_paid
where validflag=1
and C.CLNTNUM = age_band.COWNNUM
and c.CLNTNUM = total_paid.COWNNUM
and c.cltdod = 99999999 --condition for death'''
inputDf=pd.read_csv("churnclntnum.csv",dtype={'clntnum':'str'})


# In[3]:


#getting premiums and cost as a separate dataset for each customer
'''select clntnum,premium,isnull(claimpaid,0),(premium-isnull(claimpaid,0)) net_profit
from(
select distinct clntnum,premium,
(select sum(TOTAMNT) from vm1dta.regppf p ,vm1dta.chdrpf pol where p.CHDRNUM 

=pol.chdrnum  and c.validflag=1 and pol.VALIDFLAG
=1 and pol.COWNNUM = c.CLNTNUM) claimpaid
from vm1dta.clntpf c,
(select c.cownnum,sum(acctamt) premium from vm1dta.rtrnpf r,vm1dta.chdrpf c 
where r.rldgacct=c.chdrnum and rtrim(r.sacscode)='LP' and rtrim(r.sacstyp)='S' and 

c.validflag=1 and r.BATCTRCDE='B522'
group by c.cownnum) total_paid
where CLTTYPE='P' and CLTIND ='C' and validflag=1
and c.CLNTNUM = total_paid.COWNNUM)t'''
premiumDf=pd.read_csv("netprofitclntnum.csv",dtype={'clntnum':'str'})


# In[4]:


#data set for coordinates , to be mapped to client region for now
regionDf=pd.read_csv("coordinates.csv")
regionDf.drop('region_code',inplace=True,axis=1)
regionDf['clientregion']=[name.upper().strip(' ') for name in regionDf.province]

inputDf['clientregion']=[name.upper().strip(' ') for name in inputDf.clientregion]
# In[5]:


#model will not require the customer number, but would be required to merge with output
modelDf=inputDf.drop('clntnum',axis=1)
modelDf.drop('client_name',inplace=True,axis=1)
#modelDf=modelDf.merge(regionDf,how='left',on='clientregion')
modelDf.occpcode.fillna('ANYS',inplace=True)
modelDf.amtpaid.fillna('medium value',inplace=True)
modelDf.drop('clientregion',inplace=True,axis=1)
'''modelDf.drop('province',inplace=True,axis=1)
modelDf.drop('latitude',inplace=True,axis=1)
modelDf.drop('longitude',inplace=True,axis=1)'''

inputDfCoordinates=inputDf.merge(regionDf,how='left',on='clientregion')

# In[6]:

lb=LabelEncoder()


# In[7]:


modelDf['cltsex']=lb.fit_transform(modelDf['cltsex'])
modelDf['marryd']=lb.fit_transform(modelDf['marryd'])
modelDf['occpcode']=lb.fit_transform(modelDf['occpcode'])
modelDf['amtpaid']=lb.fit_transform(modelDf['amtpaid'])
modelDf['entry_age']=lb.fit_transform(modelDf['entry_age'])
#modelDf.latitude.fillna(value=0,inplace=True)
#modelDf.longitude.fillna(value=0,inplace=True)
#modelDf.head(100)


# In[8]:



corr=modelDf.corr()

sns.heatmap(corr,annot=True,cmap=plt.cm.Reds)

#plt.show()


# In[9]:


cor_target = abs(corr["churn"])
print(cor_target)
relevant_features = cor_target[cor_target>0.1]
print(relevant_features) 


# In[10]:


cph = CoxPHFitter()
print('output from show progress')
print('///////////////////////////////////')
cph.fit(modelDf, duration_col='elapseddays', event_col='churn',show_progress=True,step_size=0.1)
print('//////////////////////////////////')
cph.print_summary()


# In[11]:


#cph.plot()


# In[12]:


cph.check_assumptions(modelDf,show_plots=True)


# In[13]:


#survival function only required for censored subjects,ie. customers who have not churned yet. 
notChurnedCustomers= modelDf[modelDf['churn']==0]
censoredTimeElapse=notChurnedCustomers.elapseddays


# In[14]:


values=modelDf.entry_age.unique()
#cph.plot_covariate_groups('entry_age', values=values,cmap='coolwarm')


# In[15]:

#to be computed for 5 years to extract all type of policies that fall under 5 yrs renewal term
results=cph.predict_survival_function(notChurnedCustomers,times=[365,730,1095,1460,1825],conditional_after=censoredTimeElapse)


# In[16]:


outputDf=results.transpose().merge(modelDf,how='right',left_index=True,right_index=True)
outputDf['clntnum']=inputDf['clntnum']


# In[17]:


values=modelDf.marketbased.unique()
cph.plot_covariate_groups('marketbased', values=values,cmap='coolwarm')


# In[18]:


cltvDf=outputDf.merge(premiumDf,on='clntnum')


# In[19]:


cltvDf['cltvscore']=((cltvDf['net_profit']*cltvDf[365])/(1+0.12))+((cltvDf['net_profit']*cltvDf[730])/(1+0.11)**2)+((cltvDf['net_profit']*cltvDf[1095])/(1+0.1)**3)+((cltvDf['net_profit']*cltvDf[1460])/(1+0.09)**4)+((cltvDf['net_profit']*cltvDf[1825])/(1+0.08)**5)
+(cltvDf['net_profit']/(cltvDf['elapseddays']/365))*(cltvDf['elapseddays']/365)


# In[20]:


cltvDf['percentile']=cltvDf['cltvscore'].rank(pct=True,method='max')*100


# In[21]:


def cltvBandFn(percentile):
    if (percentile >= 0 and percentile < 30):
        return 'low value'
    else:
        if (percentile > 30 and percentile < 60):
            return 'medium value'
        else:
            return 'high value'


# In[26]:


cltvDf['cltvband']=cltvDf.percentile.apply(cltvBandFn)
csvDf=cltvDf.merge(inputDfCoordinates[['client_name','cltsex','marryd','occpcode','latitude','longitude']],right_index=True,left_index=True)

# In[27]:

csvDf.to_csv("EX_SOURCE_CLTVSCORE_LIFE.csv",index=False)

