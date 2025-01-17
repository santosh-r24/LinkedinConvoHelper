# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [2.0.3] - 2024-11-08
 
Updates pushed in this commit.
### Added
- Landing page instructing users on what this is about, this only appears if users are logged out
### Changed
- The debug message which says if users exceed rate limits, instead of hardcoding the ratelimit
- Default message in chatinput is changed
- Changed the button name from submit to Generate Questions
- Added helper tooltip on what each st.file_upload is meant for
### Fixed
### Removed

## [2.0.2] - 2024-10-28
 
Updates pushed in this commit.
### Added
### Changed
- Moved prompts to .toml file 
- Initialised all varialbes in utils.initialize_variables function
### Fixed
- Warnings raised due to empty label of st.file_upload.
### Removed

## [2.0.1] - 2024-10-22
 
Updates pushed in this commit.
### Added
- Question suggestions to ask and their prompts.
### Changed
### Fixed
### Removed

## [2.0.0] - 2024-10-22
 
Updates pushed in this commit.
### Added
- pre-loading of user_pdf.
- if the user asks irrelevant questions, the LLM spits on the user's face. 
### Changed
### Fixed
### Removed


## [1.0.4] - 2024-10-09
Updates pushed in this commit.
### Added
- An alert if the user refreshes the screen. Best way to do would be if we can save session data. Too much work.
### Changed
- Message_count being retrieved from DB rather than cache. Works fine :)
### Fixed
- Saving rows properly in users and messages table.
### Removed

## [1.0.3] - 2024-10-08
Updates pushed in this commit.
 
### Added
- Changed the message count function to update after every message.
- If the user logs in again, the sidebar will be disabled and an error message will be displayed if the user has reached the message quota.
### Changed
### Fixed
- The users had to click submit 2 times in order for the chat to work. Fixed that. 
### Removed
### TODO
- Retrive User pdf and preload- have some trouble here.
- Check DB saves. 


## [1.0.2] - 2024-10-06
 
Updates pushed in this commit.
 
### Added
### Changed
### Fixed
### Removed
- Removed few shot examples from system behavior
### TO ADD
- Check message count while hitting response, rather than calling function every x seconds
- Display an appropriate message when message rate runs out 
- Retrieval user pdf and preload
- Check that the user pdf and messages are saved 
## [1.0.1] - 2024-10-02
 
- Added the user and guest pdf to session state.
- Created a side bar and moved the upload inside it. 
- Added bg color to login button.
- Created a chat interface.
- After hitting submit, model's first response is displayed.
- Added a condittion in get_llm_response to use the user's prompts and context.
- STUCK: When user asks a question that is not related to the guest, it still answers, even after giving the prompt: "If the user asks about something that is not related to the guest's profile, kindly ask them to ask something relevant."
- STUCK: When user asks something about the guest, it asnwers "Please provide me with the following information to generate relevant questions about ...."


## [1.0.0] - 2024-09-19
 
Updates pushed in this commit.
 
### Added
- Initial commit to repo
### Changed
### Fixed
### Removed