# Kinsu BR/AR Website

Welcome to the **Kinsu.mx** website repository. Kinsu is an **insurtech** expanding into **Brazil** and **Argentina**, offering innovative insurance solutions.

## Tech Stack

This project is built using the following technologies:

- **HTML5** – Markup structure for the website.
- **Vanilla JavaScript** – Client-side interactivity.
- **Directus** – Headless CMS for content management.
- **Docker** – Containerized environment for seamless deployment.
- **Nginx** – Reverse proxy and static file serving.
- **Python Server** – Backend service for specific functionalities.
- **Certificates Container** – Handles SSL/TLS certificates.

## Project Structure

The application is composed of **three main Docker containers**:

1. **Nginx** – Serves the frontend and acts as a reverse proxy.
2. **Directus** – Manages content and APIs.
3. **Python Server** – Handles backend logic.
4. **Certificates** – Manages SSL/TLS security.

## Setup & Installation

### Prerequisites
Ensure you have the following installed:
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Running the Project
1. Clone the repository:
   ```sh
   git clone https://github.com/your-org/kinsu-website.git
   cd kinsu-website
   ```
2. Start the services using Docker Compose:
   ```sh
   docker-compose up -d
   ```
3. The website should be accessible at `http://localhost` (or the configured domain).

## Development

- Modify frontend files in the `public/` directory.
- Directus CMS is accessible at `http://localhost/admin`.
- Python backend logic resides in `python_server/`.

### Stopping the Services
To stop the running containers, use:
```sh
docker-compose down
```

## Contributing

We welcome contributions! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`feature/your-feature`).
3. Commit your changes.
4. Push to your branch and submit a pull request.

## License
This project is licensed under the MIT License.

## Contact
For any inquiries, reach out at [tom@skylinecodew](mailto:tom@skylinecodew.com).


