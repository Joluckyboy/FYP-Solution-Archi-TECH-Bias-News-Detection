from classes import AWS_AGENT, GCP_AGENT

def main():
    print("starting deployment")

    # aws = AWS_AGENT()
    # aws.test()
    
    gcp = GCP_AGENT(
        project_id="ctrlaltelite-dcs-sentiment",
        domain_name=""
        service_account_path="/Users/jeromelim/Downloads/CtrlAltElite\ DCS\ Sentiment.json",
    )

    

if __name__ == '__main__':
    main()