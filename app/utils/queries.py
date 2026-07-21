# app/utils/queries.py

CONTRIBUTION_CALENDAR_QUERY = """
        {
          user(login: "%s") {
            contributionsCollection {
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """