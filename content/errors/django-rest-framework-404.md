# rest_framework.exceptions.NotFound
> Encountering rest_framework.exceptions.NotFound means a requested resource wasn't found; this guide explains how to fix it.

## What This Error Means

The `rest_framework.exceptions.NotFound` error is Django REST Framework's way of signaling an HTTP 404 "Not Found" response. It's raised when a client requests a specific resource, but that resource cannot be located by the API. Fundamentally, it means your DRF view attempted to retrieve an object from the database using a given lookup parameter (like a primary key or a slug), and no such object matched the criteria.

In essence, this exception translates Django's `Http404` or an ORM `DoesNotExist` exception into a standardized API response. When you see this, it indicates a failure at the data lookup layer within your DRF view.

## Why It Happens

This error primarily occurs because the underlying data query failed to return an object. This isn't usually an application crash, but rather a deliberate signal from DRF that the requested resource simply isn't there. It's a common and expected response for malformed or outdated requests for specific objects.

The most common scenarios involve:
1.  **Incorrect Identifier:** The client provided a primary key (PK), slug, or other lookup value that does not correspond to an existing object in the database.
2.  **Missing Resource:** The resource previously existed but has since been deleted.
3.  **Filtered Out:** The object *does* exist in the database, but your view's `get_queryset()` method or custom `get_object()` logic filters it out, making it appear non-existent to the current request.
4.  **URL Misconfiguration:** While less common for direct `NotFound`, a misconfigured URL pattern could sometimes lead to the wrong lookup field being used, or no lookup field at all, resulting in a lookup failure.

## Common Causes

In my experience, `NotFound` exceptions in DRF usually boil down to one of these specific issues:

*   **Invalid Primary Key (PK) or Lookup Field in Request:** This is by far the most frequent cause. A client sends a request to an endpoint like `/api/products/99/` but there is no product with `id=99` in the database. Or, if `lookup_field = 'slug'`, they send `/api/products/non-existent-slug/`.
*   **Resource No Longer Exists:** The object with the requested ID was valid at one point but has been deleted. This is common in systems with high churn or when managing cached client data that becomes stale.
*   **Custom `get_queryset()` Filtering:** Your view might be overriding `get_queryset()` to restrict objects based on user permissions, tenancy, or other business logic. If the requested object falls outside these restrictions for the current user, it will be filtered out, and `get_object()` will subsequently fail to find it, leading to `NotFound`. I've seen this in production when a user tries to access a resource that belongs to a different tenant, and the `get_queryset` correctly restricts access.
*   **Incorrect `lookup_field` Configuration:** Your `ModelViewSet` or `GenericAPIView` might be configured to use a specific `lookup_field` (e.g., `'slug'`), but your URL pattern is expecting a `pk` (e.g., `<int:pk>`), or vice-versa. This mismatch causes the lookup to fail because DRF is searching by the wrong attribute.
*   **Database Replication Lag:** In distributed database systems, especially with read replicas, it's possible for an object to be written to the primary database but not yet propagated to a replica that your API service is querying. A quick fetch might succeed on the primary but fail on a slightly delayed replica. This is rare but important to keep in mind in high-scale environments.

## Step-by-Step Fix

Troubleshooting `rest_framework.exceptions.NotFound` follows a logical path, primarily focusing on validating the request and the data lookup process.

### 1. Verify the Client Request

Start at the source. What did the client *actually* send?

*   **Check the URL Path Parameters:** Is the ID, slug, or other identifier in the URL path correct?
    *   **Example:** If your endpoint is `/api/users/<int:pk>/`, are you sending a valid integer that corresponds to an existing user?
*   **Examine the HTTP Request:** Use browser developer tools (Network tab), Postman, Insomnia, or `curl` to confirm the exact URL and any parameters.

    ```bash
    # Example: Check a GET request for a non-existent product
    curl -v http://localhost:8000/api/products/999/
    ```

    Pay close attention to the response status (should be 404) and any DRF error details.

### 2. Inspect Your DRF View and Serializer

The next step is to look at how your DRF view is configured to retrieve objects.

*   **`lookup_field` in `ModelViewSet` or `GenericAPIView`:**
    *   Does your view have `lookup_field` set? If so, is it `'pk'`, `'slug'`, or something else? Does this match what the URL expects?
    *   By default, `lookup_field` is `'pk'`.

*   **`get_queryset()` Method:**
    *   Is your `get_queryset()` method filtering the results in a way that might exclude the object you're trying to retrieve? Add `print()` statements or use a debugger (`pdb`) inside `get_queryset` to see what objects are being returned before the `get_object` call.

*   **Custom `get_object()` Method:**
    *   If you've overridden `get_object()`, examine its logic carefully. Is it correctly retrieving the object based on the `lookup_url_kwarg`?

    ```python
    # Example: Debugging a custom get_object
    import pdb

    class MyCustomDetailView(generics.RetrieveAPIView):
        queryset = MyModel.objects.all()
        serializer_class = MyModelSerializer
        lookup_field = 'slug'

        def get_object(self):
            # pdb.set_trace() # Uncomment to debug
            queryset = self.filter_queryset(self.get_queryset())
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            
            assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
            )

            filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
            obj = get_object_or_404(queryset, **filter_kwargs)
            
            # Additional logic or assertions here
            print(f"Attempted lookup with: {filter_kwargs}")
            print(f"Object found: {obj}")

            return obj
    ```

### 3. Verify Object Existence in the Database

This is a critical step: does the object *actually* exist with the identifier you're using?

*   **Django Shell:** Open a Django shell and query your model directly.

    ```python
    # In your project directory:
    python manage.py shell

    # Inside the shell:
    from your_app.models import MyModel

    # Check for a specific primary key
    try:
        obj = MyModel.objects.get(pk=999)
        print(f"Object found: {obj}")
    except MyModel.DoesNotExist:
        print("Object with pk=999 does not exist.")

    # Or for a slug
    try:
        obj = MyModel.objects.get(slug='non-existent-slug')
        print(f"Object found: {obj}")
    except MyModel.DoesNotExist:
        print("Object with slug='non-existent-slug' does not exist.")
    ```

    This will confirm whether the object exists and which specific lookup field it has.

### 4. Review URL Patterns (`urls.py`)

Ensure your URL configuration correctly captures the lookup field and passes it to your view.

*   **Named URL Parameters:** Make sure the name in your URL pattern (e.g., `<int:pk>`, `<str:slug>`) matches the `lookup_field` or the `lookup_url_kwarg` in your view.

    ```python
    # In your_project/urls.py or your_app/urls.py
    from django.urls import path
    from your_app.views import MyModelDetailView

    urlpatterns = [
        # Correctly named 'pk' for a primary key lookup
        path('api/mymodels/<int:pk>/', MyModelDetailView.as_view(), name='mymodel-detail'),
        # Correctly named 'slug' for a slug lookup
        path('api/products/<str:slug>/', ProductDetailView.as_view(), name='product-detail'),
    ]
    ```

    A common mistake is having `path('api/mymodels/<int:id>/', ...)` while your view expects `pk` or `slug`.

### 5. Consider Permissions or Complex Filtering

While DRF often raises `PermissionDenied` explicitly, if your `get_queryset()` or custom `get_object()` logic implicitly filters based on permissions or other complex criteria, and the object is removed from the queryset, it will result in `NotFound`.

*   **Temporarily Disable Filters:** As a debugging step, try simplifying your `get_queryset()` or temporarily removing complex permission logic to see if the object then becomes discoverable. If it does, your filtering is the culprit.

## Code Examples

Here are some concise, copy-paste ready code examples illustrating common fixes or configurations.

### 1. Correct `lookup_field` in a `ModelViewSet`

This example shows how to configure a `ModelViewSet` to use a `slug` instead of the default `pk` for object lookup.

```python
# your_app/views.py
from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug' # <--- This is the key change
    # The URL pattern for this viewset would typically be like:
    # path('products/<str:slug>/', ProductViewSet.as_view({'get': 'retrieve'}))
```

### 2. Custom `get_object()` in `RetrieveAPIView`

For more granular control or complex lookup logic, you might override `get_object()`. This example retrieves an object by `user_id` and `item_id`.

```python
# your_app/views.py
from rest_framework import generics
from rest_framework.exceptions import NotFound
from .models import UserItem
from .serializers import UserItemSerializer

class UserItemDetailView(generics.RetrieveAPIView):
    serializer_class = UserItemSerializer

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        item_id = self.kwargs.get('item_id')

        if not user_id or not item_id:
            raise NotFound("User ID and Item ID are required for this lookup.")

        try:
            # Assuming UserItem model has 'user_id' and 'item_id' fields
            obj = UserItem.objects.get(user_id=user_id, item_id=item_id)
        except UserItem.DoesNotExist:
            raise NotFound(detail=f"UserItem with user_id={user_id} and item_id={item_id} not found.")
        
        # Add permission checks here if necessary
        self.check_object_permissions(self.request, obj)
        return obj

# urls.py for the above view:
# path('users/<int:user_id>/items/<int:item_id>/', UserItemDetailView.as_view(), name='user-item-detail'),
```

## Environment-Specific Notes

The troubleshooting steps remain largely the same across environments, but how you gather information can differ.

*   **Local Development:**
    *   **Debugging is Easiest:** Use `pdb` (as shown above), `print()` statements, or IDE debuggers.
    *   **Django Debug Toolbar:** An invaluable tool for local development, showing queries, context, and request details. It can quickly highlight if your `get_queryset` is returning an empty set.
    *   **Direct Database Access:** You have immediate access to your local database (SQLite, PostgreSQL, MySQL) to confirm object existence.

*   **Docker/Containerized Environments:**
    *   **Logs are Key:** `docker logs <container_name>` will be your primary source of error messages and `print()` output. Ensure your logging level is appropriate.
    *   **Network Configuration:** Double-check that containers can communicate (e.g., your DRF app container can reach your database container). A networking issue might prevent the app from even querying the DB, leading to implicit `NotFound` if `get_object` can't get past `queryset.first()`.
    *   **Environment Variables:** Verify that database connection strings, `DEBUG` settings, and other environment variables are correctly passed to the container.

*   **Cloud (AWS, GCP, Azure, etc.):**
    *   **Centralized Logging:** Rely heavily on cloud logging services (e.g., AWS CloudWatch, Google Cloud Logging/Stackdriver, Azure Monitor). Filter logs for the specific endpoint and error.
    *   **Monitoring and Tracing:** Tools like AWS X-Ray or Google Cloud Trace can help visualize the flow of a request and pinpoint where the `NotFound` originated (e.g., which microservice, which database call failed).
    *   **API Gateway/Load Balancer Configuration:** Ensure that your API Gateway or Load Balancer is correctly routing requests to your application instances and not modifying path parameters in an unexpected way.
    *   **Database Replication Lag:** In large-scale cloud deployments, be aware of potential delays in database replication to read replicas. If a resource is created and immediately requested from a replica, it might genuinely not be found yet.
    *   **CDN Caching:** If you have a CDN in front of your API, ensure it's not caching 404 responses for too long or inappropriately.

## Frequently Asked Questions

*   **Q: Can `rest_framework.exceptions.NotFound` be caused by permissions?**
    *   **A:** Rarely directly for the `NotFound` exception itself. DRF typically raises `rest_framework.exceptions.PermissionDenied` (HTTP 403 Forbidden) when a user lacks permissions to access an *existing* resource. However, if your `get_queryset()` method filters based on permissions and the desired object is removed from the resulting queryset, then `get_object()` will subsequently fail to find it, resulting in `NotFound`. In such cases, the object is effectively "not found" *for that specific user*.

*   **Q: How can I customize the error response for `NotFound`?**
    *   **A:** You can define a custom exception handler in your `settings.py`. This allows you to catch `rest_framework.exceptions.NotFound` and return a custom JSON structure or message to the client.

    ```python
    # settings.py
    REST_FRAMEWORK = {
        'EXCEPTION_HANDLER': 'your_app.utils.custom_exception_handler',
    }

    # your_app/utils.py
    from rest_framework.views import exception_handler
    from rest_framework.response import Response
    from rest_framework import status

    def custom_exception_handler(exc, context):
        # Call REST framework's default exception handler first,
        # to get the standard error response.
        response = exception_handler(exc, context)

        # Customize the response for NotFound
        if isinstance(exc, status.HTTP_404_NOT_FOUND):
            custom_response_data = {
                'status': 'error',
                'message': 'The requested resource could not be found. Please check the identifier.',
                'code': 'RESOURCE_NOT_FOUND',
            }
            response.data = custom_response_data
            response.status_code = status.HTTP_404_NOT_FOUND

        return response
    ```

*   **Q: Why do I get `NotFound` even when the object clearly exists in the database?**
    *   **A:** This usually points to a mismatch between the lookup mechanism and the actual data.
        1.  **Wrong `lookup_field`:** Your view might be looking by `pk` while the URL sends a `slug`, or vice-versa.
        2.  **`get_queryset()` filtering:** Your queryset is inadvertently filtering out the object.
        3.  **URL pattern issue:** The URL might not be capturing the lookup parameter correctly, or it's being passed with the wrong name to the view.
        4.  **Database state:** Less common, but replication lag or an outdated database snapshot could cause this in distributed systems.

*   **Q: Is Django's `DoesNotExist` the same as DRF's `NotFound`?**
    *   **A:** They are related but distinct. `DoesNotExist` is a standard Django ORM exception raised when `get()` fails to find an object. DRF's `NotFound` is an `APIException` that wraps an `Http404` (which itself can be raised by `get_object_or_404`), translating the underlying Django ORM or HTTP error into a consistent API error response (HTTP 404).

## Related Errors

*   `rest_framework.exceptions.PermissionDenied` (HTTP 403 Forbidden)
*   `rest_framework.exceptions.MethodNotAllowed` (HTTP 405 Method Not Allowed)
*   `django.http.Http404`
*   `YourModel.DoesNotExist` (a Django ORM exception)