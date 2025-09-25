import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, List, ListItem, 
  ListItemText, IconButton, Dialog, DialogTitle, 
  DialogContent, DialogActions, FormControl, InputLabel,
  Select, MenuItem, Divider, Chip, Grid, Paper
} from '@mui/material';
import { Add, Edit, Delete, Send } from '@mui/icons-material';
import axios from 'axios';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function Templates({ onSelectTemplate, selectedChat }) {
  // State
  const [templates, setTemplates] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState(null);
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('General');
  const [categories, setCategories] = useState(['General', 'Business', 'Personal']);
  const [variables, setVariables] = useState({});
  const [fillDialogOpen, setFillDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Load templates on component mount
  useEffect(() => {
    loadTemplates();
  }, []);
  
  // Load templates from API
  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/templates`);
      if (response.data && response.data.templates) {
        setTemplates(response.data.templates);
        
        // Extract unique categories
        const uniqueCategories = [...new Set(response.data.templates.map(t => t.category))];
        setCategories(['General', 'Business', 'Personal', ...uniqueCategories.filter(c => !['General', 'Business', 'Personal'].includes(c))]);
      }
    } catch (error) {
      console.error('Error loading templates:', error);
      setError('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };
  
  // Open create/edit dialog
  const openDialog = (template = null) => {
    if (template) {
      // Edit existing template
      setEditTemplate(template);
      setName(template.name);
      setContent(template.content);
      setCategory(template.category || 'General');
    } else {
      // Create new template
      setEditTemplate(null);
      setName('');
      setContent('');
      setCategory('General');
    }
    setDialogOpen(true);
  };
  
  // Close dialog
  const closeDialog = () => {
    setDialogOpen(false);
    setEditTemplate(null);
  };
  
  // Save template
  const saveTemplate = async () => {
    if (!name || !content) {
      setError('Name and content are required');
      return;
    }
    
    setLoading(true);
    try {
      if (editTemplate) {
        // Update existing template
        await axios.post(`${API_BASE_URL}/templates`, {
          name,
          content,
          category
        });
      } else {
        // Create new template
        await axios.post(`${API_BASE_URL}/templates`, {
          name,
          content,
          category
        });
      }
      
      // Reload templates
      await loadTemplates();
      closeDialog();
    } catch (error) {
      console.error('Error saving template:', error);
      setError('Failed to save template');
    } finally {
      setLoading(false);
    }
  };
  
  // Delete template
  const deleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }
    
    setLoading(true);
    try {
      await axios.delete(`${API_BASE_URL}/templates/${templateId}`);
      await loadTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      setError('Failed to delete template');
    } finally {
      setLoading(false);
    }
  };
  
  // Open fill template dialog
  const openFillDialog = (template) => {
    setSelectedTemplate(template);
    
    // Extract variables from template content
    const variableRegex = /{([^}]+)}/g;
    const matches = template.content.match(variableRegex) || [];
    
    // Create variables object with empty values
    const vars = {};
    matches.forEach(match => {
      const varName = match.replace(/{|}/g, '');
      vars[varName] = '';
    });
    
    setVariables(vars);
    setFillDialogOpen(true);
  };
  
  // Close fill template dialog
  const closeFillDialog = () => {
    setFillDialogOpen(false);
    setSelectedTemplate(null);
    setVariables({});
  };
  
  // Fill template and use it
  const fillAndUseTemplate = async () => {
    if (!selectedTemplate) return;
    
    try {
      const response = await axios.post(`${API_BASE_URL}/templates/${selectedTemplate.id}/fill`, {
        variables
      });
      
      if (response.data && response.data.content) {
        // Pass filled template to parent component
        onSelectTemplate(response.data.content);
        closeFillDialog();
      }
    } catch (error) {
      console.error('Error filling template:', error);
      setError('Failed to fill template');
    }
  };
  
  // Extract variables from template content
  const extractVariables = (content) => {
    const variableRegex = /{([^}]+)}/g;
    const matches = content.match(variableRegex) || [];
    return matches.map(match => match.replace(/{|}/g, ''));
  };
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Message Templates</Typography>
        <Button 
          variant="contained" 
          startIcon={<Add />} 
          onClick={() => openDialog()}
          disabled={loading}
        >
          New Template
        </Button>
      </Box>
      
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      
      {/* Template Categories */}
      <Box sx={{ mb: 2 }}>
        <Grid container spacing={1}>
          {categories.map((cat) => (
            <Grid item key={cat}>
              <Chip 
                label={cat} 
                onClick={() => {}} 
                variant="outlined" 
              />
            </Grid>
          ))}
        </Grid>
      </Box>
      
      {/* Template List */}
      <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
        <List>
          {templates.length === 0 ? (
            <ListItem>
              <ListItemText primary="No templates found" />
            </ListItem>
          ) : (
            templates.map((template) => (
              <React.Fragment key={template.id}>
                <ListItem
                  secondaryAction={
                    <Box>
                      <IconButton 
                        edge="end" 
                        onClick={() => openDialog(template)}
                        disabled={loading}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton 
                        edge="end" 
                        onClick={() => deleteTemplate(template.id)}
                        disabled={loading}
                      >
                        <Delete />
                      </IconButton>
                      <IconButton 
                        edge="end" 
                        onClick={() => openFillDialog(template)}
                        disabled={loading || !selectedChat}
                      >
                        <Send />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemText 
                    primary={template.name} 
                    secondary={
                      <>
                        <Typography variant="body2" color="text.secondary">
                          {template.content.length > 50 
                            ? `${template.content.substring(0, 50)}...` 
                            : template.content}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Category: {template.category || 'General'}
                        </Typography>
                        {extractVariables(template.content).length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            {extractVariables(template.content).map((variable) => (
                              <Chip 
                                key={variable} 
                                label={variable} 
                                size="small" 
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                          </Box>
                        )}
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
      
      {/* Create/Edit Template Dialog */}
      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editTemplate ? 'Edit Template' : 'Create Template'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Template Name"
            fullWidth
            value={name}
            onChange={(e) => setName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={category}
              label="Category"
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((cat) => (
                <MenuItem key={cat} value={cat}>{cat}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            label="Template Content"
            fullWidth
            multiline
            rows={4}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            helperText="Use {variable} syntax for placeholders, e.g., 'Hello {name}'"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={loading}>Cancel</Button>
          <Button onClick={saveTemplate} disabled={loading}>Save</Button>
        </DialogActions>
      </Dialog>
      
      {/* Fill Template Dialog */}
      <Dialog open={fillDialogOpen} onClose={closeFillDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Fill Template Variables
        </DialogTitle>
        <DialogContent>
          {selectedTemplate && (
            <>
              <Typography variant="subtitle1" gutterBottom>
                {selectedTemplate.name}
              </Typography>
              <Typography variant="body2" gutterBottom>
                {selectedTemplate.content}
              </Typography>
              <Divider sx={{ my: 2 }} />
              {Object.keys(variables).length > 0 ? (
                Object.keys(variables).map((varName) => (
                  <TextField
                    key={varName}
                    margin="dense"
                    label={varName}
                    fullWidth
                    value={variables[varName]}
                    onChange={(e) => setVariables({...variables, [varName]: e.target.value})}
                    sx={{ mb: 1 }}
                  />
                ))
              ) : (
                <Typography variant="body2">
                  This template has no variables to fill.
                </Typography>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeFillDialog} disabled={loading}>Cancel</Button>
          <Button onClick={fillAndUseTemplate} disabled={loading}>Use Template</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Templates;
