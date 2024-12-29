# Timea Classic

**Timea Classic** is a Django-based e-commerce platform designed for a baby shop. It provides a seamless shopping experience with features like product search, user authentication, product variants, and a fully functional shopping cart.

---

## Features

### Core Features
- **Homepage**: Displays featured products and categories.
- **Authentication**: User registration, login, logout, and profile management.
- **Product Management**:
  - Categories and variants for organizing products.
  - Product details with reviews and dynamic star ratings.
- **Cart Management**: Add, update, and remove items from the cart.
- **Search Functionality**: Quickly find products by name or category.
- **Product Reviews**: Users can rate products and leave feedback.
- **Product Categories**: Users can rate products and leave feedback
- **orders**: Users can place orders and receive feedback.

### Planned Features
- **User Profiles**: Allow users to update their details.
- **Payment Integration**: Enable secure payment processing (e.g., Stripe, PayPal).
- **Order Management**: Track order history and view invoice generation.

---

## Technologies Used

- **Backend**: Django 4.x
- **Frontend**: HTML, CSS , JavaScript, react js
- **Database**: PostgreSQL
- **Version Control**: Git & GitHub
- **Deployment**: PythonAnywhere

---

## Project Structure

- **Core App**: Handles authentication, homepage, and settings.
- **Products App**: Manages product listings, product categories, and product variants.
- **Cart App**: Handles cart logic and processes the checkout.
- **Reviews App**: Manages product reviews and dynamic ratings.
- **Order App**: Handles order logic and processes the checkout.


---

## Installation


### Prerequisites

Before starting, make sure you have the following installed:

- Python (>= 3.8)
- PostgreSQL
- Git

To set up the project locally, follow these steps:

1. **Clone the project repository:**
 
   ```git clone https://github.com/bryansine/Timea_classic.git```
   
2.  Navigate to the project directory:
  ``` cd timea_classic/```
3. Create a Virtual Environment:
 ``` python3 -m venv myvenv```
4.  Activate the Virtual Environment (macOS/Linux):
  ```source myvenv/bin/activate```
5.  Install Required Packages:
 ``` pip install -r requirements.txt```
6.  Migrate the Database:
  ```python manage.py migrate```
7.  Create a Super User:
  ```python manage.py createsuperuser```
8.  Start the Development Server:
 ``` python3 manage.py runserver```


## Contributing

I welcome contributions from the community. If you encounter any bugs or have feature requests, please submit them through GitHub issues.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Author:** Bryan Sine
**LinkedIn:** [Bryan Sine](https://www.linkedin.com/in/bryansine)
