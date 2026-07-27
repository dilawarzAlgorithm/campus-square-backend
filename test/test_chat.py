import pytest

def test_cannot_dm_self(client, auth_headers, test_verified_user):
    user_id = test_verified_user.id
    response = client.post(f"/api/chat/dm/{user_id}", headers=auth_headers)
    assert response.status_code == 400
    assert "yourself" in response.json()["detail"]

def test_create_and_fetch_dm(client, auth_headers, test_other_user):
    target_id = test_other_user.id
    response = client.post(f"/api/chat/dm/{target_id}", headers=auth_headers)
    assert response.status_code == 200
    conv_id = response.json()["id"]
    assert response.json()["type"] == "DM"
    
    response_again = client.post(f"/api/chat/dm/{target_id}", headers=auth_headers)
    assert response_again.status_code == 200
    assert response_again.json()["id"] == conv_id

def test_get_my_conversations(client, auth_headers, test_other_user):
    target_id = test_other_user.id
    client.post(f"/api/chat/dm/{target_id}", headers=auth_headers)
    
    response = client.get("/api/chat/conversations", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert "unread_count" in response.json()[0]

def test_block_participant(client, auth_headers_staff, auth_headers, test_other_user, test_department):
    response = client.post(f"/api/chat/dm/{test_other_user.id}", headers=auth_headers_staff)
    conv_id = response.json()["id"]
    
    block_response = client.patch(
        f"/api/chat/conversations/{conv_id}/participants/{test_other_user.id}/block",
        json={"is_blocked": True},
        headers=auth_headers_staff
    )
    assert block_response.status_code == 200
    assert block_response.json()["is_blocked"] is True
    
    fail_response = client.patch(
        f"/api/chat/conversations/{conv_id}/participants/{test_other_user.id}/block",
        json={"is_blocked": True},
        headers=auth_headers
    )
    assert fail_response.status_code == 403

def test_forward_message_and_get_messages(client, auth_headers, test_other_user):
    dm_resp = client.post(f"/api/chat/dm/{test_other_user.id}", headers=auth_headers)
    conv_id = dm_resp.json()["id"]
    
    msg_resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"content": "Hello there!"},
        headers=auth_headers
    )
    assert msg_resp.status_code == 200
    assert msg_resp.json()["success"] is True
    
    get_msgs = client.get(f"/api/chat/conversations/{conv_id}/messages", headers=auth_headers)
    assert get_msgs.status_code == 200
    assert len(get_msgs.json()) >= 1
    assert get_msgs.json()[0]["content"] == "Hello there!"

def test_get_global_unread_count(client, auth_headers):
    response = client.get("/api/chat/unread-count", headers=auth_headers)
    assert response.status_code == 200
    assert "unread_count" in response.json()

def test_delete_message(client, auth_headers, auth_headers_other_user, test_other_user):
    dm_resp = client.post(f"/api/chat/dm/{test_other_user.id}", headers=auth_headers)
    conv_id = dm_resp.json()["id"]
    
    client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"content": "Delete me!"},
        headers=auth_headers
    )
    
    get_msgs = client.get(f"/api/chat/conversations/{conv_id}/messages", headers=auth_headers)
    msg_id = get_msgs.json()[0]["id"]
    
    del_fail = client.delete(f"/api/chat/messages/{msg_id}", headers=auth_headers_other_user)
    assert del_fail.status_code == 403
    
    del_resp = client.delete(f"/api/chat/messages/{msg_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True