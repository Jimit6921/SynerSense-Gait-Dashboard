import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io, base64

def make_graph(pre_df, post_df):
    gait = np.linspace(0,100,101)

    def resample(s):
        x = np.linspace(0,100,len(s))
        return np.interp(gait, x, s)

    plt.figure(figsize=(8,5))
    plt.plot(gait, resample(pre_df["LHipAngles_Sag_Z"]), 'r--', label="Pre")
    plt.plot(gait, resample(post_df["LHipAngles_Sag_Z"]), 'b', label="Post")
    plt.title("Hip Flexion")
    plt.xlabel("Gait %")
    plt.ylabel("Angle")
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    return base64.b64encode(buf.getvalue()).decode()
