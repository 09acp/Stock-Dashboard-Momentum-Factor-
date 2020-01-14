# SNP STOCK DASHBOARD - Momentum Factor
Alex Papa 23/07/2019

-------------------------------------------------------
FILES NOT INCLUDED (Confidentiality Reasons)
- database.db  -sqlite
- raw Excel Data

__Should work with Yahoo Finance price data with modifications__

-------------------------------------------------------

#### __Stage 1__
- [x] DATA WRANGLING
  - [toolbox.py](https://github.com/09acp/Stock-Dashboard-Momentum-Factor-/blob/master/toolbox.py)
    - Contains all main functions for building momentum factor.

  - [initial_wrangler.py](https://github.com/09acp/Stock-Dashboard-Momentum-Factor-/blob/master/initial_wrangler.py)
    - Wrangles excel spreadsheet data to clean raw data
    - Uses functions from toolbox.py
    - Stores/retrieves information for sql 'database'

#### __Stage 2__
- [x] MOMENTUM INDICATOR
  - [main.py](https://github.com/09acp/Stock-Dashboard-Momentum-Factor-/blob/master/__main__.py)
    - script that builds the Momentum Indicator
    - uses functions from toolbox
    - Structures Dataset into desired format
    - Calculates Compounded Returns for entire Index and by week
    - Calculates Compounded Returns by Company by week
    - Calculates Z-Scores for each window by Company and by week
    -  Generates Company Scores
      -  CALCULATE AVG & STD OF COMPANY AVG_Z_SCORE
      -  CALCULATE Z-SCORES 2# FOR EACH COMPANY BY WEEK
      -  FOR EACH WEEK ASSIGN COMPANY TO QUINTILE ACCORDING TO Z-SCORE
    - Generates Compounded Returns by Quintile and create Quintile Indices
    - CALCULATES COMPOUNDED RETURNS BY WEEK FOR EACH QUINTILE
    - Generates Relative Compounded Quintile Returns

#### __Stage 3__
- [x] DASHBOARD VISUALISATION
  - [app.py](https://github.com/09acp/Stock-Dashboard-Momentum-Factor-/blob/master/app.py)
    - script that creates interactive web-based plots
    - using Plotly Dash (Python)
    - For increased efficiency call data from database.db

  -------------------------------------------------------

#### Other Files
- Various materials from intership at Barings London



#### __Issues__
S1
- ...
  - ...

S2
- ...
  - ...

#### Additional Ideas
- ...
  - ...
