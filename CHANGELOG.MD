# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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