# ------------------------ IMPORTS
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px

# ------------------------ SET CONFIG

# setting the page title, icon and opening in wide mode
st.set_page_config(page_title = "China Goods Trade", page_icon = 'cn',layout="wide")

# ------------------------ STARTING DASHBOARD

### LOADING IN DATA FROM OUR TEST FILE

# setup a function to load in data and preprocess that can be cached
# show spinner as False to remove yellow notification from top
@st.cache(show_spinner=False)
def start_dashboard():
    
    # load one large dataframe from our files
    df1 = pd.read_csv('df_m1.csv',dtype=str)
    df2 = pd.read_csv('df_m2.csv',dtype=str)
    df3 = pd.read_csv('df_m3.csv',dtype=str)
    df4 = pd.read_csv('df_m4.csv',dtype=str)
    df5 = pd.read_csv('df_m5.csv',dtype=str)
    df6 = pd.read_csv('df_m6.csv',dtype=str)
    
    df = pd.concat([df1,df2,df3,df4,df5,df6])
    
    df = df[['date', 'Flow', 'Country', 'HS2_code', 'HS2_desc', 'Trade_Value',
                   'Sec_code', 'Sec_desc', 'Continent']]
    
    # handle datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # convert trade values to numeric
    df['Trade_Value'] = pd.to_numeric(df['Trade_Value'])
    
    return df

# start it
df = start_dashboard()

# ------------------------ WRITING AN INTRO

st.write('# Dashboard for Exploring Chinese Goods Trade with the world')
st.write('---')
st.write("This dashboard uses data collected from [China Customs Interactive Database](http://43.248.49.97/indexEn) to explore China's trade with international partners at the HS2 Digit level. By default the charts will show monthly trade values, but this can be changed to a rolling monthly sum using the slider in the sidebar. The dataset includes data from 2017 through to 2022, by default charts will show all of the data available given the metrics used for that chart (year on year differences and rolling values will lose some preceeding data-points) but the preferred start/end year to be shown on charts can also be set in the axis. For relevant sections, you can use the selectors to choose which trade partners you would like to examine and the graphs will automatically update to show a selection of relevant visuals.")
st.write('---')

# ------------------------ ADDING A sidebar for rolling & Month Axis selection

# set a slider to select rolling value in sidebar
rol_val = st.sidebar.slider('Monthly Rolling Sum (set as "1" for no rolling)', min_value=1, max_value=12, value=12)

# handle how to describe period in titles
# can reuse this across many titles
period = 'Monthly'
if rol_val > 1:
    period = f"rolling {rol_val}M Sum"

# setting a yearly range to be diplayed on the axis
# set as two separate slides for min and max
min_year = st.sidebar.slider('Date Range - Minimum', 
                                   min_value=df.date.min().year, 
                                   max_value=df.date.max().year,
                                   value=df.date.min().year
                                  )

max_year = st.sidebar.slider('Date Range - Maximum', 
                                   min_value=df.date.min().year, 
                                   max_value=df.date.max().year,
                                  value=df.date.max().year
                                  )
# convert the min and max years to strings so can use with .loc to index plots for x-axis
min_year = str(min_year)
max_year = str(max_year)

# setup selection in sidebar for if we want custom end date on bar plots
latest_custom = st.sidebar.selectbox('For bar charts and tree maps, show latest data or through to custom month', ['Latest', 'Custom'], index=0)


# ------------------------ ADDING 3 CHARTS FOR WORLD TRADE AT TOP

st.write("### China's Global Trade")
st.write("This section looks at China's global exports and imports, showing absolute values as well as growth in terms of both % change yoy and USD change yoy. By default monthly trade is shown but a rolling sum of your choice can be set using the slider in the sidebar.")

activate_global = st.checkbox("Would you like to explore global trade?")

if activate_global == True:

    # add everything together into just imports and exports using groupby
    # reset index at the end
    df_world = df.groupby(['date', 'Flow'])['Trade_Value'].sum().reset_index()

    # create a pivot so can plot as time series
    df_world_pivot = df_world.pivot(index='date', columns='Flow', values='Trade_Value')
    
    
    # create two columns so can make grid of three charts
    col1, col2 = st.columns((1,1))

    with col1:
        # plot a chart of absolute values (top-left of 2x2 grid)
        fig = px.line(df_world_pivot.rolling(rol_val).sum().dropna().loc[min_year:max_year], title=f"China's global trade, {period}, USD billions")
        fig.update_layout(xaxis_title='', yaxis_title='US Dollars')
        st.plotly_chart(fig, use_container_width=True)

        # plot a chart of diff yoy (bottom-left of 2x2 grid)
        fig = px.line(df_world_pivot.rolling(rol_val).sum().diff(12).dropna().loc[min_year:max_year], title=f"China's global trade, {period}, USD billions change yoy")
        fig.update_layout(xaxis_title='', yaxis_title='USD change yoy')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # plot a chart of % change yoy (top-right of 2x2 grid)
        fig = px.line(df_world_pivot.rolling(rol_val).sum().pct_change(12).mul(100).round(2).dropna().loc[min_year:max_year], title=f"China's global trade, {period}, % change yoy")
        fig.update_layout(xaxis_title='', yaxis_title='% change yoy')
        st.plotly_chart(fig, use_container_width=True)


# ------------------------ ADDING 6 CHARTS ON CHINA'S IMPORTS FROM CHOSEN SELECTION FOR ALL PARTNERS

# start Imports section plotting
st.write('---')
st.write("### China's total imports from selected partners")
st.write("This section shows China's total imports from a customisable selection of partners, on an individual trade partner basis. The line charts show abosolute values of imports as well as growth in both % change yoy and USD change yoy terms. By default, monthly import values will be shown but a customised rolling monthly sum can be setup in the sidebar. The bar charts also show absolute values and the two growth metrics, but for a given point in time. By default, they show data (monthly or a rolling monthly sum) for/through-to the latest month available. This can also be changed by selecting a custom end-date for bar charts in the sidebar, and then choosing the end month from a new box which will appear atop the relevant chart.")

# adding a checkbox so this section can be turned on or off
activate_partners_im = st.checkbox("Would you like to explore China's total imports by trading partners?")

# if the box is checked then we activate partner selection, subsetting and plotting
if activate_partners_im == True:
    
    ##-- Setup multi-selection 

    # creating a list of unique partners
    list_unique_partners = list(set(df['Country']))
    list_unique_partners.sort()

    # creating a list of default partners
    list_default_partners = ['United Kingdom', 'Germany', 'France']

    # setup partners selection multi-select box
    partners_selection_im = st.multiselect("Which of China's trade partners would you like to explore for imports?", list_unique_partners, default=list_default_partners)

    ##-- Subset the df by this selection, create an imports only time series dataframe
    
    # creating a Boolean condition based on our partners selection, and creating new df
    chosen_partners_condition = df['Country'].isin(partners_selection_im)
    df_partners = df[chosen_partners_condition]

    # filter into imports only dataframe
    df_partners_im = df_partners[df_partners['Flow'] == 'Imports']

    # group inot total imports dataframe
    df_partners_im_ttl = df_partners_im.groupby(['date', 'Country'])['Trade_Value'].sum().reset_index()

    # create a pivot so can plot as time series
    df_partners_im_ttl_pivot = df_partners_im_ttl.pivot(index='date', columns='Country', values='Trade_Value')

    ##-- Handle rolling / monthly section of plot title

    # setup title to use in bar charts
    if rol_val > 1:
        bar_title = f"{rol_val}M rolling sum through to "
    else:
        bar_title = ''

    #---- ROW OF PLOTS FOR ABSOLUTE VALUES

    col1, col2 = st.columns((1,1))

    with col1: 

        # plot a chart of absolute values
        # manipulate accordingle, create plotly figure and give to streamlit
        plot_df = df_partners_im_ttl_pivot.rolling(rol_val).sum().dropna().loc[min_year:max_year]
        fig = px.line(plot_df, 
                       title=f"China's Imports from selected partners, {period}, US Dollars")
        fig.update_layout(xaxis_title='', yaxis_title='US Dollars')
        st.plotly_chart(fig, use_container_width=True)

    with col2:

        # bar chart % year
        # takes the same basic time series manipulations as df in other column
        df_for_bar = plot_df 
        if latest_custom == 'Latest':
            df_for_bar = df_for_bar.iloc[-1,:].sort_values()
        else:
            end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
            df_for_bar = df_for_bar.loc[end_month].sort_values()


        fig = px.bar(df_for_bar, orientation='h', 
                       title=f"China's Imports from selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, US Dollars")
        fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    #---- ROW OF PLOTS FOR % CHANGE YOY

    col1, col2 = st.columns((1,1))

    with col1:

        # plot a chart of % change yoy
        plot_df = df_partners_im_ttl_pivot.rolling(rol_val).sum().pct_change(12).mul(100).round(2).dropna().loc[min_year:max_year]
        fig = px.line(plot_df, title=f"China's Imports to selected partners, {period}, % change yoy")
        fig.update_layout(xaxis_title='', yaxis_title='% change yoy')
        st.plotly_chart(fig, use_container_width=True)

    with col2:

        # bar chart % year
        df_for_bar = plot_df
        if latest_custom == 'Latest':
            df_for_bar = df_for_bar.iloc[-1,:].sort_values()
        else:
            end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
            df_for_bar = df_for_bar.loc[end_month].sort_values()
        fig = px.bar(df_for_bar, orientation='h', 
                       title=f"China's Imports from selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, % change yoy")
        fig.update_layout(xaxis_title='% change yoy', yaxis_title='', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    #---- ROW OF PLOTS FOR USD CHANGE YOY    

    col1, col2 = st.columns((1,1))

    with col1:  

        # plot a chart of diff yoy
        plot_df = df_partners_im_ttl_pivot.rolling(rol_val).sum().diff(12).dropna().loc[min_year:max_year]
        fig = px.line(plot_df, title=f"China's Imports to selected partners, {period}, USD change yoy")
        st.plotly_chart(fig, use_container_width=True)

    with col2:   

        # bar chart diff over year
        df_for_bar = plot_df
        if latest_custom == 'Latest':
            df_for_bar = df_for_bar.iloc[-1,:].sort_values()
        else:
            end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
            df_for_bar = df_for_bar.loc[end_month].sort_values()
        fig = px.bar(df_for_bar, orientation='h', 
                       title=f"China's Imports from selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, USD change yoy")
        fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
#------------------------ IMPORTS FOR A SUBSET OF PRODUCTS, CHOOSE TO INCLUDE OR EXCLUDE

# start Imports section plotting
st.write('---')
st.write("### China's total imports from selected partners, for a reduced subset of products.")
st.write("This section is for examining subsets of China's imports across selected partners, with subsets of products to be included or excluded at the HS 2 digit category. This section will not show the trade in individual HS2 categories, it will agregate the selected subset into a total figure. The selection of trade partners to be compared is preserved from the previous section. For selecting which HS2 categories to include in the aggregation, you can choose to begin with all HS2 digit categories and choose which to exclude; or you can choose to begin with no categories and gradually include HS2 categories. Like the previous section, line charts will then display absolute values and growth metrics, while bar charts will display the same values but at a specific point in time. Rolling sums, axis and (for bar charts) point-in-time selections can be made in the same way as previous sections.")

activate_imports_partners_subset = st.checkbox('Would you like to activate imports by partner for a custom subset of import products?')

if activate_imports_partners_subset == True:

    ##-- repeat the subsetting by partners code from last section
    
    # creating a list of unique partners
    list_unique_partners = list(set(df['Country']))
    list_unique_partners.sort()

    # creating a list of default partners
    list_default_partners = ['United Kingdom', 'Germany', 'France']

    # setup partners selection multi-select box, so can run independently of last section
    partners_selection_im_ss = st.multiselect("Which of China's trade partners would you like to explore for a subset of imports?", list_unique_partners, default=list_default_partners)

    # creating a Boolean condition based on our partners selection, and creating new df
    chosen_partners_condition = df['Country'].isin(partners_selection_im_ss)
    df_partners = df[chosen_partners_condition]

    # filter into separate export and import dataframes
    df_partners_im = df_partners[df_partners['Flow'] == 'Imports']
    
    ##-- choose whether to include / exclude
    
    # now ask whether would like to begin by including or excluding
    exclude_include_im = st.selectbox("Would you like to gradually include or exclude HS2 categories", ['Not selected', 'Include', 'Exclude'], index=0)

    # only activate if something is selected
    if exclude_include_im != 'Not selected':

        # create a list of unique HS2 codes
        list_unique_commodities = list(set(df['HS2_desc']))
        list_unique_commodities.sort()
        
        # setup full or empty starting conditions based on if exclude / include ticked
        if exclude_include_im == 'Exclude': 
            starting_list = list_unique_commodities
        else:
            starting_list = []

        # create a multi-selector for products, which begins as full or empty depending on Include or Exclude
        products_selection_im_ss = st.multiselect("Which products would you like to be included in the analysis: click / type to add, or click to remove?", list_unique_commodities, default=starting_list)

        # creating a Boolean condition based on our products selection, and creating new df
        chosen_products_condition = df_partners_im['HS2_desc'].isin(products_selection_im_ss)
        df_products_im = df_partners_im[chosen_products_condition]

        # group this into total imports
        df_products_im_ttl = df_products_im.groupby(['date', 'Country'])['Trade_Value'].sum().reset_index()

        # create a pivot so can plot as time series
        df_partners_im_ttl_pivot = df_products_im_ttl.pivot(index='date', columns='Country', values='Trade_Value')

        ### -- now setup plots
        
        # condition that must have at least one product selected, so empty plots don't show
        if len(products_selection_im_ss) == 0:
            st.write('Please select some products!')
        else:
            
            ##-- Handle rolling / monthly section of plot title

            # setup title to use in bar charts
            if rol_val > 1:
                bar_title = f"{rol_val}M rolling sum through to "
            else:
                bar_title = ''

            #---- ROW OF PLOTS FOR ABSOLUTE VALUES

            col1, col2 = st.columns((1,1))

            with col1: 

                # plot a chart of absolute values
                # manipulate accordingle, create plotly figure and give to streamlit
                plot_df = df_partners_im_ttl_pivot.rolling(rol_val).sum().dropna().loc[min_year:max_year]
                fig = px.line(plot_df, 
                               title=f"China's Imports from selected partners, {period}, US Dollars")
                fig.update_layout(xaxis_title='', yaxis_title='US Dollars')
                st.plotly_chart(fig, use_container_width=True)

            with col2:

                # bar chart % year
                # takes the same basic time series manipulations as df in other column
                df_for_bar = plot_df 
                if latest_custom == 'Latest':
                    df_for_bar = df_for_bar.iloc[-1,:].sort_values()
                else:
                    end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
                    df_for_bar = df_for_bar.loc[end_month].sort_values()


                fig = px.bar(df_for_bar, orientation='h', 
                               title=f"China's Imports from selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, US Dollars")
                fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            #---- ROW OF PLOTS FOR % CHANGE YOY

            col1, col2 = st.columns((1,1))

            with col1:

                # plot a chart of % change yoy
                plot_df = df_partners_im_ttl_pivot.rolling(rol_val).sum().pct_change(12).mul(100).round(2).dropna().loc[min_year:max_year]
                fig = px.line(plot_df, title=f"China's Imports to selected partners, {period}, % change yoy")
                fig.update_layout(xaxis_title='', yaxis_title='% change yoy')
                st.plotly_chart(fig, use_container_width=True)

            with col2:

                # bar chart % year
                df_for_bar = plot_df
                if latest_custom == 'Latest':
                    df_for_bar = df_for_bar.iloc[-1,:].sort_values()
                else:
                    end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
                    df_for_bar = df_for_bar.loc[end_month].sort_values()
                fig = px.bar(df_for_bar, orientation='h', 
                               title=f"China's Imports from selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, % change yoy")
                fig.update_layout(xaxis_title='% change yoy', yaxis_title='', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            #---- ROW OF PLOTS FOR USD CHANGE YOY    

            col1, col2 = st.columns((1,1))

            with col1:  

                # plot a chart of diff yoy
                plot_df = df_partners_im_ttl_pivot.rolling(rol_val).sum().diff(12).dropna().loc[min_year:max_year]
                fig = px.line(plot_df, title=f"China's Imports to selected partners, {period}, USD change yoy")
                st.plotly_chart(fig, use_container_width=True)

            with col2:   

                # bar chart diff over year
                df_for_bar = plot_df
                if latest_custom == 'Latest':
                    df_for_bar = df_for_bar.iloc[-1,:].sort_values()
                else:
                    end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
                    df_for_bar = df_for_bar.loc[end_month].sort_values()
                fig = px.bar(df_for_bar, orientation='h', 
                               title=f"China's Imports from selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, USD change yoy")
                fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)


# ------------------------ PLOTTING TOTAL EXPORTS

# ------------------------ ADDING 6 CHARTS ON CHINA'S EXPORTS TO CHOSEN SELECTION FOR ALL PARTNERS

# start Exports section plotting
st.write('---')
st.write("### China's total exports to selected partners")
st.write("This section shows China's total exports to a customisable selection of partners, on an individual trade partner basis. The line charts show abosolute values of exports as well as growth in both % change yoy and USD change yoy terms. By default, monthly export values will be shown but a customised rolling monthly sum can be setup in the sidebar. The bar charts also show absolute values and the two growth metrics, but for a given point in time. By default, they show data (monthly or a rolling monthly sum) for/through-to the latest month available. This can also be changed by selecting a custom end-date for bar charts in the sidebar, and then choosing the end month from a new box which will appear atop the relevant chart.")

# adding a checkbox so this section can be turned on or off
activate_partners_ex = st.checkbox("Would you like to explore China's exports by trading partners?")

# if the box is checked then we activate partner selection, subsetting and plotting
if activate_partners_ex == True:
    
    ##-- Setup multi-selection 

    # creating a list of unique partners
    list_unique_partners = list(set(df['Country']))
    list_unique_partners.sort()

    # creating a list of default partners
    list_default_partners = ['United Kingdom', 'Germany', 'France']

    # setup partners selection multi-select box
    partners_selection_ex = st.multiselect("Which of China's trade partners would you like to explore for exports?", list_unique_partners, default=list_default_partners)

    ##-- Subset the df by this selection, create an exports only time series dataframe
    
    # creating a Boolean condition based on our partners selection, and creating new df
    chosen_partners_condition = df['Country'].isin(partners_selection_ex)
    df_partners = df[chosen_partners_condition]

    # filter into separate export dataframe
    df_partners_ex = df_partners[df_partners['Flow'] == 'Exports']

    # group this into total exports
    df_partners_ex_ttl = df_partners_ex.groupby(['date', 'Country'])['Trade_Value'].sum().reset_index()

    # create a pivot so can plot as time series
    df_partners_ex_ttl_pivot = df_partners_ex_ttl.pivot(index='date', columns='Country', values='Trade_Value')

    ##-- Handle rolling / monthly section of plot title

    # setup title to use in bar charts
    if rol_val > 1:
        bar_title = f"{rol_val}M rolling sum through to "
    else:
        bar_title = ''

    #---- ROW OF PLOTS FOR ABSOLUTE VALUES

    col1, col2 = st.columns((1,1))

    with col1: 

        # plot a chart of absolute values
        # manipulate accordingle, create plotly figure and give to streamlit
        plot_df = df_partners_ex_ttl_pivot.rolling(rol_val).sum().dropna().loc[min_year:max_year]
        fig = px.line(plot_df, 
                       title=f"China's Exports to selected partners, {period}, US Dollars")
        fig.update_layout(xaxis_title='', yaxis_title='US Dollars')
        st.plotly_chart(fig, use_container_width=True)

    with col2:

        # bar chart % year
        # takes the same basic time series manipulations as df in other column
        df_for_bar = plot_df 
        if latest_custom == 'Latest':
            df_for_bar = df_for_bar.iloc[-1,:].sort_values()
        else:
            end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
            df_for_bar = df_for_bar.loc[end_month].sort_values()


        fig = px.bar(df_for_bar, orientation='h', 
                       title=f"China's Exports to selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, US Dollars")
        fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    #---- ROW OF PLOTS FOR % CHANGE YOY

    col1, col2 = st.columns((1,1))

    with col1:

        # plot a chart of % change yoy
        plot_df = df_partners_ex_ttl_pivot.rolling(rol_val).sum().pct_change(12).mul(100).round(2).dropna().loc[min_year:max_year]
        fig = px.line(plot_df, title=f"China's Exports to selected partners, {period}, % change yoy")
        fig.update_layout(xaxis_title='', yaxis_title='% change yoy')
        st.plotly_chart(fig, use_container_width=True)

    with col2:

        # bar chart % year
        df_for_bar = plot_df
        if latest_custom == 'Latest':
            df_for_bar = df_for_bar.iloc[-1,:].sort_values()
        else:
            end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
            df_for_bar = df_for_bar.loc[end_month].sort_values()
        fig = px.bar(df_for_bar, orientation='h', 
                       title=f"China's Exports to selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, % change yoy")
        fig.update_layout(xaxis_title='% change yoy', yaxis_title='', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    #---- ROW OF PLOTS FOR USD CHANGE YOY    

    col1, col2 = st.columns((1,1))

    with col1:  

        # plot a chart of diff yoy
        plot_df = df_partners_ex_ttl_pivot.rolling(rol_val).sum().diff(12).dropna().loc[min_year:max_year]
        fig = px.line(plot_df, title=f"China's Exports to selected partners, {period}, USD change yoy")
        st.plotly_chart(fig, use_container_width=True)

    with col2:   

        # bar chart diff over year
        df_for_bar = plot_df
        if latest_custom == 'Latest':
            df_for_bar = df_for_bar.iloc[-1,:].sort_values()
        else:
            end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
            df_for_bar = df_for_bar.loc[end_month].sort_values()
        fig = px.bar(df_for_bar, orientation='h', 
                       title=f"China's Exports to selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, USD change yoy")
        fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
#------------------------ EXPORTS FOR A SUBSET OF PRODUCTS, CHOOSE TO INCLUDE OR EXCLUDE

# start exports section plotting
st.write('---')
st.write("### China's total exports to selected partners, for a reduced subset of products.")
st.write("This section is for examining subsets of China's exports across selected partners, with subsets of products to be included or excluded at the HS 2 digit category. This section will not show the trade in individual HS2 categories, it will agregate the selected subset into a total figure. For selecting which HS2 categories to include in the aggregation, you can choose to begin with all HS2 digit categories and choose which to exclude; or you can choose to begin with no categories and gradually include HS2 categories. Like the previous section, line charts will then display absolute values and growth metrics, while bar charts will display the same values but at a specific point in time. Rolling sums, axis and (for bar charts) point-in-time selections can be made in the same way as previous sections.")

activate_exports_partners_subset = st.checkbox('Would you like to explore exports by partner for a custom subset of export products?')

if activate_exports_partners_subset == True:

    ##-- repeat the subsetting by partners code from last section
    
    # creating a list of unique partners
    list_unique_partners = list(set(df['Country']))
    list_unique_partners.sort()

    # creating a list of default partners
    list_default_partners = ['United Kingdom', 'Germany', 'France']

    # setup partners selection multi-select box, so can run independently of last section
    partners_selection_ex_ss = st.multiselect("Which of China's trade partners would you like to explore?", list_unique_partners, default=list_default_partners)

    # creating a Boolean condition based on our partners selection, and creating new df
    chosen_partners_condition = df['Country'].isin(partners_selection_ex_ss)
    df_partners = df[chosen_partners_condition]

    # filter into exports only dataframe
    df_partners_ex = df_partners[df_partners['Flow'] == 'Exports']
    
    ##-- choose whether to include / exclude
    
    # now ask whether would like to begin by including or excluding
    exclude_include_ex = st.selectbox("Would you like to gradually include or exclude HS2 categories", ['Not selected', 'Include', 'Exclude'], index=0)

    # only activate if something is selected
    if exclude_include_ex != 'Not selected':

        # create a list of unique HS2 codes
        list_unique_commodities = list(set(df['HS2_desc']))
        list_unique_commodities.sort()
        
        # setup full or empty starting conditions based on if exclude / include ticked
        if exclude_include_ex == 'Exclude': 
            starting_list = list_unique_commodities
        else:
            starting_list = []

        # create a multi-selector for products, which begins as full or empty depending on Include or Exclude
        products_selection_ex_ss = st.multiselect("Which products would you like to be included in the analysis: click / type to add, or click to remove?", list_unique_commodities, default=starting_list)

        # creating a Boolean condition based on our products selection, and creating new df
        chosen_products_condition = df_partners_ex['HS2_desc'].isin(products_selection_ex_ss)
        df_products_ex = df_partners_ex[chosen_products_condition]

        # group this into total exports
        df_products_ex_ttl = df_products_ex.groupby(['date', 'Country'])['Trade_Value'].sum().reset_index()

        # create a pivot so can plot as time series
        df_partners_ex_ttl_pivot = df_products_ex_ttl.pivot(index='date', columns='Country', values='Trade_Value')

        ### -- now setup plots
        
        # condition that must have at least one product selected, so empty plots don't show
        if len(products_selection_ex_ss) == 0:
            st.write('Please select some products!')
        else:
            
            ##-- Handle rolling / monthly section of plot title

            # setup title to use in bar charts
            if rol_val > 1:
                bar_title = f"{rol_val}M rolling sum through to "
            else:
                bar_title = ''


            #---- ROW OF PLOTS FOR ABSOLUTE VALUES

            col1, col2 = st.columns((1,1))

            with col1: 

                # plot a chart of absolute values
                # manipulate accordingle, create plotly figure and give to streamlit
                plot_df = df_partners_ex_ttl_pivot.rolling(rol_val).sum().dropna().loc[min_year:max_year]
                fig = px.line(plot_df, 
                               title=f"China's Exports to selected partners, {period}, US Dollars")
                fig.update_layout(xaxis_title='', yaxis_title='US Dollars')
                st.plotly_chart(fig, use_container_width=True)

            with col2:

                # bar chart % year
                # takes the same basic time series manipulations as df in other column
                df_for_bar = plot_df 
                if latest_custom == 'Latest':
                    df_for_bar = df_for_bar.iloc[-1,:].sort_values()
                else:
                    end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
                    df_for_bar = df_for_bar.loc[end_month].sort_values()


                fig = px.bar(df_for_bar, orientation='h', 
                               title=f"China's Exports to selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, US Dollars")
                fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            #---- ROW OF PLOTS FOR % CHANGE YOY

            col1, col2 = st.columns((1,1))

            with col1:

                # plot a chart of % change yoy
                plot_df = df_partners_ex_ttl_pivot.rolling(rol_val).sum().pct_change(12).mul(100).round(2).dropna().loc[min_year:max_year]
                fig = px.line(plot_df, title=f"China's Exports to selected partners, {period}, % change yoy")
                fig.update_layout(xaxis_title='', yaxis_title='% change yoy')
                st.plotly_chart(fig, use_container_width=True)

            with col2:

                # bar chart % year
                df_for_bar = plot_df
                if latest_custom == 'Latest':
                    df_for_bar = df_for_bar.iloc[-1,:].sort_values()
                else:
                    end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
                    df_for_bar = df_for_bar.loc[end_month].sort_values()
                fig = px.bar(df_for_bar, orientation='h', 
                               title=f"China's Exports to selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, % change yoy")
                fig.update_layout(xaxis_title='% change yoy', yaxis_title='', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            #---- ROW OF PLOTS FOR USD CHANGE YOY    

            col1, col2 = st.columns((1,1))

            with col1:  

                # plot a chart of diff yoy
                plot_df = df_partners_ex_ttl_pivot.rolling(rol_val).sum().diff(12).dropna().loc[min_year:max_year]
                fig = px.line(plot_df, title=f"China's Exports to selected partners, {period}, USD change yoy")
                st.plotly_chart(fig, use_container_width=True)

            with col2:   

                # bar chart diff over year
                df_for_bar = plot_df
                if latest_custom == 'Latest':
                    df_for_bar = df_for_bar.iloc[-1,:].sort_values()
                else:
                    end_month = st.selectbox('Show trade ending in which month?', df_for_bar.index, index= len(df_for_bar.index) - 1)
                    df_for_bar = df_for_bar.loc[end_month].sort_values()
                fig = px.bar(df_for_bar, orientation='h', 
                               title=f"China's Exports to selected partners, {bar_title}{df_for_bar.name.month_name()} {df_for_bar.name.year}, USD change yoy")
                fig.update_layout(xaxis_title='US Dollars', yaxis_title='', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)


#------------------------ CHINA's GLOBAL TRADE BY SECTION AND HS2

st.write('---')
st.write("### China's Global Trade by HS product category")
st.write("This section looks at China's global trade broken down by HS Section and HS2 digit category, showing absolute values of trade. By default latest monthly trade values are shown but a rolling sum of your choice can be set using the slider in the sidebar; and the specific date can also be set.")

activate_global_by_product = st.checkbox("Would you like to explore global trade by HS Product Categories?")

if activate_global_by_product  == True:

    # add everything together into just imports and exports using groupby
    # reset index at the end
    df_world_hs = df.groupby(['date', 'Flow', 'Sec_desc','HS2_desc'])['Trade_Value'].sum().reset_index()

    # create a pivot so can apply rolling and set as plot as time series
    df_world_hs_pivot = df_world_hs.pivot(index=['Flow','Sec_desc','HS2_desc'], columns='date', values='Trade_Value')
    
    # transpose it, apply our rolling value    
    df_world_hs_pivot = df_world_hs_pivot.T.rolling(rol_val).sum().dropna().T
    
    # grab the latest time period for title, use this directly for latest or will be updated if custom date
    period_for_tree_title = df_world_hs_pivot.columns[-1]
    
    ##--- Plotting 
    
    # handle whether to show through to latest month, or custom month
    # since rolling is already applied, can filter the dataframes so just one column of trade values (based on Latest or custom date)
    # reset the index and rename columns to help with px treempa plotting
    if latest_custom == 'Latest':
            df_for_tree = df_world_hs_pivot.iloc[:,-1]
            df_for_tree = df_for_tree.reset_index()
            df_for_tree.columns = ['Flow','HS_Section','HS2','trade_value']
            
    else:
            end_month = st.selectbox('Show trade ending in which month?', df_world_hs_pivot.T.index, index= len(df_world_hs_pivot.T.index) - 1)
            period_for_tree_title = end_month # update this one only if go to custom
            df_for_tree = df_world_hs_pivot.T.loc[end_month].T
            df_for_tree = df_for_tree.reset_index()
            df_for_tree.columns = ['Flow','HS_Section','HS2','trade_value']
            
    # setup through to bit of tile title to use in tree-maps
    if rol_val > 1:
        tree_title = f"{rol_val}M rolling sum through to "
    else:
        tree_title = ''   
    
    # plot plotly treemap
    # set the path as Flow > HS Section > HS2
    fig = px.treemap(df_for_tree, path=['Flow','HS_Section','HS2'], values='trade_value',
                    title=f"China's global trade by flow and HS Category, {tree_title}{period_for_tree_title.month_name()} {period_for_tree_title.year}, US Dollars")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)
    
    # plot for imports
    df_for_tree_im = df_for_tree[df_for_tree['Flow'] == 'Imports']
    
    fig = px.treemap(df_for_tree_im, path=['HS_Section','HS2'], values='trade_value',
                    title=f"China's global imports by HS Category, {tree_title}{period_for_tree_title.month_name()} {period_for_tree_title.year}, US Dollars")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)
    
    # plot for imports
    df_for_tree_ex = df_for_tree[df_for_tree['Flow'] == 'Exports']
    
    fig = px.treemap(df_for_tree_ex, path=['HS_Section','HS2'], values='trade_value',
                    title=f"China's global exports by HS Category, {tree_title}{period_for_tree_title.month_name()} {period_for_tree_title.year}, US Dollars")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)

    
#------------------------ CHINA's GLOBAL TRADE BY REGION AND TRADE PARTNER

st.write('---')
st.write("### China's Global Trade by region and trade partner")
st.write("This section looks at China's global trade broken down by region and trade partner, showing absolute values of trade. By default latest monthly trade values are shown but a rolling sum of your choice can be set using the slider in the sidebar; and the specific date can also be set.")

activate_global_by_region = st.checkbox("Would you like to explore global trade by region and trade partner?")

if activate_global_by_region  == True:

    # add everything together into just imports and exports using groupby
    # reset index at the end
    df_world_region = df.groupby(['date', 'Flow', 'Continent','Country'])['Trade_Value'].sum().reset_index()

    # create a pivot so can apply rolling and set as plot as time series
    df_world_region_pivot =  df_world_region.pivot(index=['Flow','Continent','Country'], columns='date', values='Trade_Value')
    
    # fill the NaNs
    df_world_region_pivot = df_world_region_pivot.fillna(0)
    
    # transpose it, apply our rolling value    
    df_world_region_pivot = df_world_region_pivot.T.rolling(rol_val).sum().dropna().T
           
    # grab the latest time period for title, use this directly for latest or will be updated if custom date
    period_for_tree_title = df_world_region_pivot.columns[-1]
    
    ##--- Plotting 
    
    # handle whether to show through to latest month, or custom month
    # since rolling is already applied, can filter the dataframes so just one column of trade values (based on Latest or custom date)
    # reset the index and rename columns to help with px treempa plotting
    if latest_custom == 'Latest':
            df_for_tree = df_world_region_pivot.iloc[:,-1]
            df_for_tree = df_for_tree.reset_index()
            df_for_tree.columns = ['Flow','Continent','Country','trade_value']
            
    else:
            end_month = st.selectbox('Show trade ending in which month?', df_world_region_pivot.T.index, index= len(df_world_region_pivot.T.index) - 1)
            period_for_tree_title = end_month # update this one only if go to custom
            df_for_tree = df_world_region_pivot.T.loc[end_month].T
            df_for_tree = df_for_tree.reset_index()
            df_for_tree.columns = ['Flow','Continent','Country','trade_value']
            
    # setup through to bit of tile title to use in tree-maps
    if rol_val > 1:
        tree_title = f"{rol_val}M rolling sum through to "
    else:
        tree_title = ''   
    
    # plot plotly treemap
    # set the path as Flow > HS Section > HS2
    fig = px.treemap(df_for_tree, path=['Flow','Continent','Country'], values='trade_value',
                    title=f"China's global trade by flow and region / trade partner, {tree_title}{period_for_tree_title.month_name()} {period_for_tree_title.year}, US Dollars")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)
    
    # plot for imports
    df_for_tree_im = df_for_tree[df_for_tree['Flow'] == 'Imports']
    
    fig = px.treemap(df_for_tree_im, path=['Continent','Country'], values='trade_value',
                    title=f"China's global imports by HS region / trade partner, {tree_title}{period_for_tree_title.month_name()} {period_for_tree_title.year}, US Dollars")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)
    
    # plot for imports
    df_for_tree_ex = df_for_tree[df_for_tree['Flow'] == 'Exports']
    
    fig = px.treemap(df_for_tree_ex, path=['Continent','Country'], values='trade_value',
                    title=f"China's global exports by HS region / trade partner, {tree_title}{period_for_tree_title.month_name()} {period_for_tree_title.year}, US Dollars")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    st.plotly_chart(fig, use_container_width=True)
    
    
    
    
    
    
    

    
 

