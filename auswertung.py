import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("dnssec_bench.csv")
x = df[df.iloc[:, 0]=="RSASHA1"]
print(x)

RSASHA1_keypair_time=[]
for wert in x.iloc[:,1]:
    if wert == "keypair":
        RSASHA1_keypair_time.append(wert)

print(RSASHA1_keypair_time)
