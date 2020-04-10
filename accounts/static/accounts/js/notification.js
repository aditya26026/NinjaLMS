function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Disable propagation for the notification dropdown: ensures it is not closed on each click
let notification_dropdown = document.getElementById("notifications_dropdown");
if (notification_dropdown) {
  notification_dropdown.addEventListener("click", function (e) {
    e.stopPropagation()
  });
}

function update_notification_counter(responseText) {
  let unread_nb = JSON.parse(responseText)['unread'];
  let counter = document.getElementById("notification_counter");
  if (counter) {
    if (unread_nb > 0) {
      counter.innerText = unread_nb;
    } else {
      counter.remove();
    }
  }
}

function notification_mark_as_read(notification_id) {
  let csrftoken = getCookie('csrftoken');
  let xhr = new XMLHttpRequest();
  xhr.open('POST', "/accounts/ajax/notification/read/" + notification_id, true);
  if (csrftoken) {
    xhr.setRequestHeader("X-CSRFToken", csrftoken);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4 && xhr.status === 200) {
        update_notification_counter(xhr.responseText);

        // Change message style
        document.getElementById("notification_" + notification_id + "_message").classList.add("text-muted");
        // Remove the button used to mark the notification as read
        document.getElementById("notification_" + notification_id + "_mark_as_read_btn").remove();
      }
    };
    xhr.send()
  } else {
    console.log('CSRF token is not set');
  }
}

function notification_delete(notification_id) {
  let csrftoken = getCookie('csrftoken');
  let xhr = new XMLHttpRequest();
  xhr.open('POST', "/accounts/ajax/notification/delete/" + notification_id, true);
  if (csrftoken) {
    xhr.setRequestHeader("X-CSRFToken", csrftoken);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4 && xhr.status === 200) {
        update_notification_counter(xhr.responseText);

        // Remove the notification and its corresponding divider
        document.getElementById("notification_" + notification_id).remove();
        let divider = document.getElementById("notification_divider_" + notification_id);
        if (divider) {
          divider.remove();
        }

        // Close the notification dropdown if there is not any notification
        let dropdown = document.getElementById("notifications_dropdown");
        if (dropdown.children.length === 0) {
          dropdown.remove()
        }
      }
    };
    xhr.send()
  } else {
    console.log('CSRF token is not set');
  }
}

