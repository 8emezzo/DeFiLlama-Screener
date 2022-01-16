import pandas as pd
import datetime
import requests
import os



##########################################################
################ CUSTOMIZABLE PARAMETERS #################
##########################################################
FILE_HTML = 'DLS.html' # path file output HTML
TVL_LIM = 1 # TVL minimum limit filter in $ millions
MY_CHAIN = ['Ethereum', 'Polygon', 'Binance', 'Terra', 'Avalanche', 'Solana', 'Fantom', 'Cronos', 'Osmosis',
 'Celo', 'Boba', 'Thorchain', 'Harmony', 'Bitcoin', 'Moonriver', 'Optimism', 'Algorand', 'Arbitrum', 'Kucoin', 'Aurora', 'Kava', 'Near', 'Moonbeam', 'Fuse'] # filter chain
N_ROW = 10 # number output row
##########################################################



if __name__ == "__main__":

        print('[1/2] Defillama data download')
        # save data on df
        df = pd.DataFrame( requests.get('https://api.llama.fi/protocols').json() )

        # capitalization index. If it is too high, the price may be too high
        df['tvl_index'] = df['mcap'] / df['tvl']
        df['tvl_index'] = df['tvl_index'].round(2)
        # capitalization index FULL, that is totally diluted, that is with all tokens created
        df['F_tvl_index'] = df['fdv'] / df['tvl']
        df['F_tvl_index'] = df['F_tvl_index'].round(2)

        # turn TVL into $ millions
        df['tvl'] = df['tvl'] / 1000000
        df['tvl'] = df['tvl'].astype(int)

        # TVL minimum limit filter in $ millions
        df = df[ df['tvl'] >= TVL_LIM ]
        #  filter chain
        df = df[ [bool(set(x) & set(MY_CHAIN)) for x in df['chains']] ]
        # filter columns
        df = df[ ['name', 'symbol' ,'url', 'chains', 'tvl', 'tvl_index', 'F_tvl_index', 'change_1h', 'change_1d', 'change_7d', 'chainTvls', 'forkedFrom',  'audits',  'category', 'address'] ]

        # column for chart link on Dexscreener
        df['chart'] = ''

        # iter df :(
        for i,r in df.iterrows():
            # get dict
            d = df.loc[i,'chainTvls']
            # change amount of individual chains tvl in $ millions
            df.at[i,'chainTvls'] = {k: int(round(v/1000000,0)) for k, v in d.items()}

            # get main chain
            chain = df.loc[i,'chains'][0].lower()
            if chain == 'binance' : chain = 'bsc'
            if chain == 'arbitrum': chain = 'ethereum'

            # contract address
            address = str(df.loc[i,'address']).rpartition(':')[-1]
            address_click = address
            if address == 'None' or address == '-' :
                address = ''
                address_click = chain

            # link chart on Dexscreener
            link = 'https://dexscreener.com/' + chain + '/' + address

            df.at[i,'chart'] = '<a href=' + link + ' target="_blank"> ' + str(df.loc[i,'symbol']) + ' ' + address_click + ' </a>'

        df.drop(columns=['address'], inplace=True)
        df.drop(columns=['symbol'], inplace=True)

        # round percentages to int
        df['change_1h'] = df['change_1h'].fillna(0.0).round().astype(int) #, errors='ignore')
        df['change_1d'] = df['change_1d'].fillna(0.0).round().astype(int)
        df['change_7d'] = df['change_7d'].fillna(0.0).round().astype(int)

        # make the link web page
        df['url'] = '<a href=' + df['url'] + ' target="_blank">'+ df['url'] +'</a>'

        # HTML pattern
        pd.set_option('colheader_justify', 'center')
        html_string = '''
        <html>
            <head><title>DeFiLlama Screener</title></head>
            <link rel="stylesheet" type="text/css" href="DLS.css"/>
            <body>
                {table}
            </body>
        </html>.
        '''

        df_h = df.sort_values(by='change_1h',ascending=False).head(N_ROW)
        df_d = df.sort_values(by='change_1d',ascending=False).head(N_ROW)
        df_w = df.sort_values(by='change_7d',ascending=False).head(N_ROW)

        mh = (df_h.change_1h.median() + df_h.change_1h.mean())/2 # average weight percentage hour
        md = (df_d.change_1d.median() + df_d.change_1d.mean())/2 # average weight percentage daily
        mw = (df_w.change_7d.median() + df_w.change_7d.mean())/2 # average weight percentage weekly

        df_sum3 = df.assign(sub_tot=df['change_1h']/mh + df['change_1d']/md + df['change_7d']/mw).sort_values(by='sub_tot',ascending=False).drop(columns=['sub_tot']).head(N_ROW)
        df_sum2 = df.assign(sub_tot=df['change_1h']/mh + df['change_1d']/md                     ).sort_values(by='sub_tot',ascending=False).drop(columns=['sub_tot']).head(N_ROW)
        df_sum1 = df.assign(sub_tot=                     df['change_1d']/md + df['change_7d']/mw).sort_values(by='sub_tot',ascending=False).drop(columns=['sub_tot']).head(N_ROW)

        df_index = df[ (df['tvl']>2) & (df['tvl_index']>0) ].sort_values(by='tvl_index', ascending=True)

        # make HTML
        with open(FILE_HTML, 'w') as f:
            f.write("</BR></pre> Update data " + datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S") )
            f.write("</BR>")
            f.write("</BR></pre> Top hour+day+week")
            f.write(html_string.format(table=df_sum3.to_html(escape=False, classes='mystyle')))
            f.write("</BR></pre> Top hour+day")
            f.write(html_string.format(table=df_sum2.to_html(escape=False, classes='mystyle')))
            f.write("</BR></pre> Top day+week")
            f.write(html_string.format(table=df_sum1.to_html(escape=False, classes='mystyle')))
            f.write("</BR></pre> Top hour")
            f.write(html_string.format(table=df_h.to_html(escape=False, classes='mystyle')))
            f.write("</BR></pre> Top day")
            f.write(html_string.format(table=df_d.to_html(escape=False, classes='mystyle')))
            f.write("</BR></pre> Top week")
            f.write(html_string.format(table=df_w.to_html(escape=False, classes='mystyle')))
            f.write("</BR></pre> tvl_mcap_index order: on head the most undervalued, at the bottom of the overestimated")
            f.write(html_string.format(table=df_index.to_html(escape=False, classes='mystyle')))

        # open HTML
        print('[2/2] Open HTML output')
        os.system("start " + FILE_HTML)
        
