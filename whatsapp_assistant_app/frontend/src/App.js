import React, { useState, useEffect } from 'react';
import { 
  Box, Container, Grid, Paper, Typography, TextField, Button, 
  List, ListItem, ListItemText, ListItemAvatar, Avatar, Divider,
  AppBar, Toolbar, IconButton, CircularProgress, Snackbar, Alert,
  Tabs, Tab
} from '@mui/material';
import { Send, Refresh, Settings, Message, Schedule, Help } from '@mui/icons-material';
import axios from 'axios';
import './App.css';

// Import custom components
import Templates from './Templates';
import Scheduler from './Scheduler';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  // State
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [apiKey, setApiKey] = useState(localStorage.getItem('llm_api_key') || '');
  const [showSettings, setShowSettings] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [useAI, setUseAI] = useState(false);

  // Check WhatsApp connection status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/status`);
        setConnected(response.data.whatsapp_connected);
      } catch (error) {
        console.error('Error checking status:', error);
        setConnected(false);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Load chats
  useEffect(() => {
    if (connected) {
      loadChats();
    }
  }, [connected]);

  // Load messages when a chat is selected
  useEffect(() => {
    if (selectedChat) {
      loadMessages(selectedChat.jid);
    }
  }, [selectedChat]);

  // Load chats from API
  const loadChats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/chats`);
      if (response.data && response.data.chats) {
        setChats(response.data.chats);
      }
    } catch (error) {
      console.error('Error loading chats:', error);
      showNotification('Error loading chats', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Load messages from API
  const loadMessages = async (chatJid) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/messages/${chatJid}?limit=50`);
      if (response.data && response.data.messages) {
        setMessages(response.data.messages);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      showNotification('Error loading messages', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Send message
  const sendMessage = async () => {
    if (!selectedChat || !newMessage.trim()) return;

    setLoading(true);
    try {
      if (useAI) {
        // Send with AI processing
        const response = await axios.post(`${API_BASE_URL}/assistant`, {
          recipient: selectedChat.jid,
          prompt: newMessage,
          api_key: apiKey
        });

        if (response.data.success) {
          // Add both messages to local state
          setMessages([
            ...messages, 
            {
              id: Date.now().toString(),
              chat_jid: selectedChat.jid,
              content: newMessage,
              timestamp: Date.now(),
              is_from_me: true
            },
            {
              id: (Date.now() + 1).toString(),
              chat_jid: selectedChat.jid,
              content: response.data.llm_response,
              timestamp: Date.now() + 1,
              is_from_me: true
            }
          ]);
          setNewMessage('');
          showNotification('AI message sent successfully', 'success');
        } else {
          showNotification(`Error: ${response.data.message}`, 'error');
        }
      } else {
        // Send regular message
        const response = await axios.post(`${API_BASE_URL}/send`, {
          recipient: selectedChat.jid,
          message: newMessage
        });

        if (response.data.success) {
          // Add message to local state
          setMessages([...messages, {
            id: Date.now().toString(),
            chat_jid: selectedChat.jid,
            content: newMessage,
            timestamp: Date.now(),
            is_from_me: true
          }]);
          setNewMessage('');
          showNotification('Message sent successfully', 'success');
        } else {
          showNotification(`Error: ${response.data.message}`, 'error');
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      showNotification('Error sending message', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Handle template selection
  const handleTemplateSelect = (content) => {
    setNewMessage(content);
    setActiveTab(0); // Switch back to chat tab
  };
  
  // Toggle AI mode
  const toggleAIMode = () => {
    setUseAI(!useAI);
  };
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Save API key
  const saveApiKey = () => {
    localStorage.setItem('llm_api_key', apiKey);
    setShowSettings(false);
    showNotification('API key saved', 'success');
  };

  // Show notification
  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  // Close notification
  const closeNotification = () => {
    setNotification({ ...notification, open: false });
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            WhatsApp Assistant
          </Typography>
          <IconButton color="inherit" onClick={() => setShowSettings(!showSettings)}>
            <Settings />
          </IconButton>
          <IconButton color="inherit" onClick={loadChats} disabled={!connected || loading}>
            <Refresh />
          </IconButton>
          {loading && <CircularProgress color="inherit" size={24} sx={{ ml: 1 }} />}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {!connected ? (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>
              WhatsApp Not Connected
            </Typography>
            <Typography paragraph>
              Please make sure the WhatsApp MCP server is running and scan the QR code to connect your WhatsApp account.
            </Typography>
            <Button variant="contained" onClick={() => window.location.reload()}>
              Refresh
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {/* Settings Panel */}
            {showSettings && (
              <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Settings
                  </Typography>
                  <TextField
                    fullWidth
                    label="LLM API Key"
                    variant="outlined"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    margin="normal"
                    type="password"
                    helperText="Enter your API key for OpenAI, Anthropic, or other LLM providers"
                  />
                  <Button variant="contained" onClick={saveApiKey} sx={{ mt: 2 }}>
                    Save Settings
                  </Button>
                </Paper>
              </Grid>
            )}

            {/* Chat List */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ height: '70vh', overflow: 'auto' }}>
                <List>
                  {chats.map((chat) => (
                    <React.Fragment key={chat.jid}>
                      <ListItem 
                        button 
                        selected={selectedChat && selectedChat.jid === chat.jid}
                        onClick={() => setSelectedChat(chat)}
                      >
                        <ListItemAvatar>
                          <Avatar>{chat.name ? chat.name[0] : '?'}</Avatar>
                        </ListItemAvatar>
                        <ListItemText 
                          primary={chat.name || chat.jid} 
                          secondary={formatTimestamp(chat.last_message_time)}
                        />
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                  {chats.length === 0 && !loading && (
                    <ListItem>
                      <ListItemText primary="No chats found" />
                    </ListItem>
                  )}
                </List>
              </Paper>
            </Grid>

            {/* Message Area */}
            <Grid item xs={12} md={8}>
              <Paper sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
                {selectedChat ? (
                  <>
                    {/* Chat Header */}
                    <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="h6">
                        {selectedChat.name || selectedChat.jid}
                      </Typography>
                      <Box>
                        <Button
                          variant={useAI ? "contained" : "outlined"}
                          color="secondary"
                          size="small"
                          onClick={toggleAIMode}
                          sx={{ mr: 1 }}
                        >
                          {useAI ? "AI Mode: ON" : "AI Mode: OFF"}
                        </Button>
                      </Box>
                    </Box>

                    {/* Tabs */}
                    <Tabs
                      value={activeTab}
                      onChange={handleTabChange}
                      variant="fullWidth"
                      sx={{ borderBottom: '1px solid #e0e0e0' }}
                    >
                      <Tab icon={<Message />} label="Chat" />
                      <Tab icon={<Schedule />} label="Schedule" />
                      <Tab icon={<Help />} label="Templates" />
                    </Tabs>

                    {/* Tab Content */}
                    {activeTab === 0 ? (
                      // Chat Tab
                      <>
                        {/* Messages */}
                        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
                          {messages.map((message) => (
                            <Box
                              key={message.id}
                              sx={{
                                display: 'flex',
                                justifyContent: message.is_from_me ? 'flex-end' : 'flex-start',
                                mb: 2
                              }}
                            >
                              <Paper
                                sx={{
                                  p: 2,
                                  maxWidth: '70%',
                                  backgroundColor: message.is_from_me ? '#dcf8c6' : '#f5f5f5'
                                }}
                              >
                                <Typography variant="body1">{message.content}</Typography>
                                <Typography variant="caption" sx={{ display: 'block', mt: 1, textAlign: 'right' }}>
                                  {formatTimestamp(message.timestamp)}
                                </Typography>
                              </Paper>
                            </Box>
                          ))}
                          {messages.length === 0 && !loading && (
                            <Box sx={{ textAlign: 'center', mt: 4 }}>
                              <Typography variant="body1">No messages yet</Typography>
                            </Box>
                          )}
                        </Box>

                        {/* Message Input */}
                        <Box sx={{ p: 2, borderTop: '1px solid #e0e0e0', display: 'flex' }}>
                          <TextField
                            fullWidth
                            placeholder={useAI ? "Type instructions for AI..." : "Type a message..."}
                            variant="outlined"
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                          />
                          <Button
                            variant="contained"
                            color="primary"
                            endIcon={<Send />}
                            onClick={sendMessage}
                            disabled={loading || !newMessage.trim()}
                            sx={{ ml: 1 }}
                          >
                            {useAI ? "AI Send" : "Send"}
                          </Button>
                        </Box>
                      </>
                    ) : activeTab === 1 ? (
                      // Schedule Tab
                      <Box sx={{ p: 2, overflowY: 'auto' }}>
                        <Scheduler selectedChat={selectedChat} />
                      </Box>
                    ) : (
                      // Templates Tab
                      <Box sx={{ p: 2, overflowY: 'auto' }}>
                        <Templates onSelectTemplate={handleTemplateSelect} selectedChat={selectedChat} />
                      </Box>
                    )}
                  </>
                ) : (
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                    <Typography variant="h6">Select a chat to start messaging</Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        )}
      </Container>

      {/* Notification */}
      <Snackbar open={notification.open} autoHideDuration={6000} onClose={closeNotification}>
        <Alert onClose={closeNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;
