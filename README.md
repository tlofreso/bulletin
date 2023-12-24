estimated parish numbers per diocese

 * Toledo: 134
 * Steubenville: 54
 * Cincinnati: 219
 * Youngstown: 115
 * Cleveland: 187
 * Columbus: 111
  
Total: 820
parishonline: 638  

A bulletin url:
`https://container.parishesonline.com/bulletins/14/0020/20230226B.pdf`

TLD / 'bulletins' / diocese ID / parish ID / Date + B (for bulletin)

## Setup

0. Python 3.12 environment
1. `pip install -r requirements.txt`
2. Populate a `.env` file.  You can get a sense of what you need from the `.env.template` file

Then to run:

```bash
set -a
source .env

# I don't think we actually have a designated entrypoint yet, but you can run
# the various script's tests now.  For example:
python notion_stuff.py
```
