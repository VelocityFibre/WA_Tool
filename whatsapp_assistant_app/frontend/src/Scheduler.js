import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, List, ListItem, 
  ListItemText, IconButton, Dialog, DialogTitle, 
  DialogContent, DialogActions, FormControl,
  Select, MenuItem, Divider, Chip, Grid, Paper,
  InputLabel, FormHelperText, Alert
} from '@mui/material';
import { Add, Delete, Schedule, CalendarToday } from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import axios from 'axios';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function Scheduler({ selectedChat }) {
  // State
  const [scheduledMessages, setScheduledMessages] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [sendTime, setSendTime] = useState(new Date(Date.now() + 3600000)); // Default to 1 hour from now
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [messageHistory, setMessageHistory] = useState([]);
  
  // Load scheduled messages when selected chat changes
  useEffect(() => {
    if (selectedChat) {
      loadScheduledMessages();
    }
  }, [selectedChat]);
  
  // Load scheduled messages from API
  const loadScheduledMessages = async () => {
    if (!selectedChat) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/schedule?recipient=${selectedChat.jid}`);
      if (response.data && response.data.scheduled_messages) {
        setScheduledMessages(response.data.scheduled_messages);
      }
    } catch (error) {
      console.error('Error loading scheduled messages:', error);
      setError('Failed to load scheduled messages');
    } finally {
      setLoading(false);
    }
  };
  
  // Load message history
  const loadMessageHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/schedule/history`);
      if (response.data && response.data.message_history) {
        setMessageHistory(response.data.message_history);
      }
    } catch (error) {
      console.error('Error loading message history:', error);
      setError('Failed to load message history');
    } finally {
      setLoading(false);
    }
  };
  
  // Open schedule dialog
  const openDialog = () => {
    setMessage('');
    setSendTime(new Date(Date.now() + 3600000)); // Default to 1 hour from now
    setDialogOpen(true);
  };
  
  // Close dialog
  const closeDialog = () => {
    setDialogOpen(false);
  };
  
  // Schedule a message
  const scheduleMessage = async () => {
    if (!selectedChat || !message) {
      setError('Chat and message are required');
      return;
    }
    
    if (sendTime <= new Date()) {
      setError('Send time must be in the future');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/schedule`, {
        recipient: selectedChat.jid,
        message,
        send_time: sendTime.toISOString(),
        metadata: {
          chat_name: selectedChat.name || selectedChat.jid
        }
      });
      
      if (response.data && response.data.success) {
        setSuccess('Message scheduled successfully');
        closeDialog();
        await loadScheduledMessages();
      } else {
        setError(response.data.message || 'Failed to schedule message');
      }
    } catch (error) {
      console.error('Error scheduling message:', error);
      setError('Failed to schedule message');
    } finally {
      setLoading(false);
    }
  };
  
  // Cancel a scheduled message
  const cancelScheduledMessage = async (messageId) => {
    if (!window.confirm('Are you sure you want to cancel this scheduled message?')) {
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.delete(`${API_BASE_URL}/schedule/${messageId}`);
      
      if (response.data && response.data.success) {
        setSuccess('Scheduled message canceled');
        await loadScheduledMessages();
      } else {
        setError(response.data.message || 'Failed to cancel scheduled message');
      }
    } catch (error) {
      console.error('Error canceling scheduled message:', error);
      setError('Failed to cancel scheduled message');
    } finally {
      setLoading(false);
    }
  };
  
  // Format date for display
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch (e) {
      return dateString;
    }
  };
  
  // Open message history dialog
  const openHistoryDialog = async () => {
    await loadMessageHistory();
    setHistoryDialogOpen(true);
  };
  
  // Close history dialog
  const closeHistoryDialog = () => {
    setHistoryDialogOpen(false);
  };
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Scheduled Messages</Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<CalendarToday />} 
            onClick={openHistoryDialog}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            History
          </Button>
          <Button 
            variant="contained" 
            startIcon={<Add />} 
            onClick={openDialog}
            disabled={loading || !selectedChat}
          >
            Schedule Message
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}
      
      {/* Scheduled Messages List */}
      <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
        <List>
          {!selectedChat ? (
            <ListItem>
              <ListItemText primary="Select a chat to view scheduled messages" />
            </ListItem>
          ) : scheduledMessages.length === 0 ? (
            <ListItem>
              <ListItemText primary="No scheduled messages for this chat" />
            </ListItem>
          ) : (
            scheduledMessages.map((msg) => (
              <React.Fragment key={msg.id}>
                <ListItem
                  secondaryAction={
                    <IconButton 
                      edge="end" 
                      onClick={() => cancelScheduledMessage(msg.id)}
                      disabled={loading}
                    >
                      <Delete />
                    </IconButton>
                  }
                >
                  <ListItemText 
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Schedule sx={{ mr: 1, fontSize: 'small', color: 'primary.main' }} />
                        <Typography variant="subtitle2">
                          Scheduled for {formatDate(msg.send_time)}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <>
                        <Typography variant="body2">
                          {msg.message.length > 100 
                            ? `${msg.message.substring(0, 100)}...` 
                            : msg.message}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Created: {formatDate(msg.created_at)}
                        </Typography>
                      </>
                    }
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))
          )}
        </List>
      </Paper>
      
      {/* Schedule Message Dialog */}
      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          Schedule Message
        </DialogTitle>
        <DialogContent>
          {selectedChat && (
            <Typography variant="subtitle1" gutterBottom>
              To: {selectedChat.name || selectedChat.jid}
            </Typography>
          )}
          
          <TextField
            autoFocus
            margin="dense"
            label="Message"
            fullWidth
            multiline
            rows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DateTimePicker
              label="Send Time"
              value={sendTime}
              onChange={(newValue) => setSendTime(newValue)}
              renderInput={(params) => <TextField {...params} fullWidth />}
              minDateTime={new Date()}
            />
          </LocalizationProvider>
          
          <FormHelperText>
            Schedule a message to be sent automatically at the specified time
          </FormHelperText>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={loading}>Cancel</Button>
          <Button 
            onClick={scheduleMessage} 
            disabled={loading || !message || !sendTime}
            variant="contained"
          >
            Schedule
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Message History Dialog */}
      <Dialog open={historyDialogOpen} onClose={closeHistoryDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          Message History
        </DialogTitle>
        <DialogContent>
          <List>
            {messageHistory.length === 0 ? (
              <ListItem>
                <ListItemText primary="No message history found" />
              </ListItem>
            ) : (
              messageHistory.map((msg) => (
                <React.Fragment key={msg.id}>
                  <ListItem>
                    <ListItemText 
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="subtitle2">
                            Sent at {formatDate(msg.sent_at)}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="body2">
                            To: {msg.metadata?.chat_name || msg.recipient}
                          </Typography>
                          <Typography variant="body2">
                            {msg.message}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Scheduled: {formatDate(msg.created_at)}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeHistoryDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Scheduler;
