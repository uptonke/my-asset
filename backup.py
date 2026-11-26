"""Legacy entry point: encrypted private storage only."""
import sys
from scripts.private_portfolio_backup import main
if __name__=="__main__":
    sys.argv.insert(1,"backup")
    main()
